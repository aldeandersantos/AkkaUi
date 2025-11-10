import json
import stripe
from server.settings import STRIPE_SECRET_KEY
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import CustomUser
from django.conf import settings
from functools import wraps
import secrets
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
import logging
 
from core.utils.date_utils import datefield_now, one_month_more, one_year_more
from message.views import notify_discord

stripe.api_key = STRIPE_SECRET_KEY



def admin_or_system_only(view_func):
    """Permite apenas admin autenticado ou chamadas internas com token."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        token = request.headers.get("X-SYSTEM-TOKEN") or request.META.get("HTTP_X_SYSTEM_TOKEN")
        if user and getattr(user, "is_authenticated", False) and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            return view_func(request, *args, **kwargs)
        if token and hasattr(settings, "INTERNAL_SYSTEM_TOKEN") and secrets.compare_digest(str(token), str(settings.INTERNAL_SYSTEM_TOKEN)):
            return view_func(request, *args, **kwargs)
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if auth_header:
            parts = auth_header.split()
            maybe_token = None
            if len(parts) == 2 and parts[0].lower() in ("bearer", "token", "signed"):
                maybe_token = parts[1]
            else:
                # allow raw token in header
                maybe_token = auth_header.strip()

            if maybe_token:
                try:
                    max_age = getattr(settings, "API_TOKEN_MAX_AGE", 3600)
                    payload = signing.loads(maybe_token, salt='usuario-api-token', max_age=max_age)
                    user_id = payload.get('user_id')
                    if user_id:
                        token_user = CustomUser.objects.filter(pk=user_id).first()
                        if token_user and (getattr(token_user, "admin", False) or getattr(token_user, "is_staff", False) or getattr(token_user, "is_superuser", False)):
                            # attach authenticated user to request for downstream code
                            request.user = token_user
                            return view_func(request, *args, **kwargs)
                except SignatureExpired:
                    return JsonResponse({"status": "error", "message": "Token expirado."}, status=401)
                except BadSignature:
                    # invalid token - fall through to permission denied
                    pass
                except Exception:
                    # inesperado - não vazar detalhes ao cliente
                    pass
        return JsonResponse({"status": "error", "message": "Permissão negada."}, status=403)
    return _wrapped


def add_vip_to_user_by_hash(hash_id: str, addition_type: str = "month"):
    """Adiciona VIP ao usuário identificado por hash_id.

    Retorna uma tupla (success: bool, message: str).
    Esta função encapsula a lógica usada por `vip_status_add` para reaproveitamento.
    """
    try:
        user = CustomUser.objects.get(hash_id=hash_id)
    except CustomUser.DoesNotExist:
        return False, "User not found"

    user.is_vip = True
    expiration_date = user.vip_expiration if user.vip_expiration else datefield_now()
    username = user.username
    if addition_type == "year":
        new_expiration_date = one_year_more(expiration_date)
        notify_discord(username, "vip", 12, "added")
    else:
        new_expiration_date = one_month_more(expiration_date)
        notify_discord(username, "vip", 1, "added")

    user.vip_expiration = new_expiration_date
    user.save()
    return True, f"VIP status added to {username} until {new_expiration_date}."

@admin_or_system_only
def vip_status_all(request):
    users = CustomUser.objects.filter(is_vip=True)
    vip_users = []
    for user in users:  
        vip_users.append({
            'username': user.username,
            'vip_expiration': user.vip_expiration,
        })
    context = { 'vip_users': vip_users }
    return JsonResponse({'vip_status_all': context})



 


@admin_or_system_only
def vip_status(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Corpo JSON inválido.'}, status=400)

    hash_id = data.get("hash")
    if not hash_id:
        return JsonResponse({'status': 'error', 'message': 'hash ausente no corpo da requisição.'}, status=400)

    try:
        user = CustomUser.objects.get(hash_id=hash_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado.'}, status=404)

    context = {
        'is_vip': user.is_vip,
        'vip_expiration': user.vip_expiration,
    }
    return JsonResponse({'vip_status': context})


@admin_or_system_only
def vip_status_add(request):
    try:
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Corpo JSON inválido.'}, status=400)

        hash_id = data.get("hash")
        if not hash_id:
            return JsonResponse({'status': 'error', 'message': 'hash ausente no corpo da requisição.'}, status=400)
        adition_type = data.get("type", "month")
        # Reutiliza a função utilitária para evitar duplicação
        success, message = add_vip_to_user_by_hash(hash_id, addition_type=adition_type)
        if not success:
            return JsonResponse({'status': 'error', 'message': message}, status=404)
        return JsonResponse({'status': 'success', 'message': message})
    except Exception as e:
        # Log internals but don't expose stacktraces to the client
        logging.exception("Erro ao adicionar VIP via vip_status_add")
        return JsonResponse({'status': 'error', 'message': 'Erro interno ao processar a requisição.'}, status=500)


@login_required
def stripe_customer_portal(request):
    # O campo customer_id deve ser salvo no seu modelo de usuário após a criação no Stripe
    user_email = request.user.email
    user_name = request.user.username
    user_obj = request.user
    stripe_customers = stripe.Customer.list(email=user_email).data
    if stripe_customers:
        customer_id = stripe_customers[0].id
    else:
        stripe_customer = stripe.Customer.create(email=user_email, name=user_name)
        customer_id = stripe_customer.id
        user_obj.stripe_customer_id = customer_id
        user_obj.save(update_fields=['stripe_customer_id'])

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri('https://www.akkaui.shop/usuario/profile/')
    )
    return redirect(session.url)
