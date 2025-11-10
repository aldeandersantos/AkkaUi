
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import stripe
from usuario.models import CustomUser
from server.settings import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

# Função para buscar dados do Stripe
def get_stripe_payment_data(session_id):
    data = {
        'stripe_available': False,
        'payment_status': None,
        'amount': None,
        'currency': None,
    }
    if not session_id:
        return data
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        data['stripe_available'] = True
        amount_total = getattr(session, 'amount_total', None)
        if amount_total is None and isinstance(session, dict):
            amount_total = session.get('amount_total')
        currency = getattr(session, 'currency', None)
        if currency is None and isinstance(session, dict):
            currency = session.get('currency')
        data['amount'] = (amount_total / 100) if amount_total else None
        data['currency'] = currency.upper() if currency else None
        status = getattr(session, 'status', None)
        if status is None and isinstance(session, dict):
            status = session.get('status')
        status_map = {
            'complete': 'completed',
            'open': 'pending',
            'expired': 'cancelled',
        }
        data['payment_status'] = status_map.get(status, status)
    except Exception as e:
        logging.exception('Erro ao recuperar Checkout Session do Stripe: %s', e)
        data['stripe_error'] = str(e)
    return data


@csrf_exempt
def stripe_checkout_subscription(request):
    import json
    data = json.loads(request.body)
    price_id = data.get('price_id')
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')
    user_id = request.user.id
    user_obj = CustomUser.objects.get(id=user_id)
    user_email = user_obj.email
    user_name = user_obj.username

    if not user_obj.is_authenticated:
        return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

    stripe_customers = stripe.Customer.list(email=user_email).data
    if stripe_customers:
        stripe_customer_id = stripe_customers[0].id
    else:
        stripe_customer = stripe.Customer.create(email=user_email, name=user_name)
        stripe_customer_id = stripe_customer.id
        user_obj.stripe_customer_id = stripe_customer_id
        user_obj.save(update_fields=['stripe_customer_id'])  
    try:
        # Se já existir um customer_id, verificar se há assinaturas ativas
        if stripe_customer_id:
            try:
                # busca assinaturas ativas (limit 1 para economia)
                active_subs = stripe.Subscription.list(customer=stripe_customer_id, status='active', limit=1).data
                if active_subs:
                    # se já existe assinatura ativa, criar sessão do Stripe Billing Portal
                    try:
                        portal_return = success_url or request.build_absolute_uri('/account/subscription/')
                        portal_session = stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url=portal_return)
                        return JsonResponse({'already_subscribed': True, 'portal_url': portal_session.url})
                    except Exception as e:
                        # Em caso de erro ao criar portal, logar e retornar mensagem amigável
                        logging.exception('Erro ao criar Stripe Billing Portal session: %s', e)
                        return JsonResponse({'already_subscribed': True, 'message': 'Usuário já possui assinatura ativa, mas não foi possível criar sessão do portal.', 'stripe_error': str(e)})
            except Exception as e:
                logging.exception('Erro ao verificar assinaturas ativas do Stripe: %s', e)
                return JsonResponse({'error': 'Erro ao verificar assinaturas ativas', 'stripe_error': str(e)}, status=500)
        # Cria sessão de checkout para assinatura
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            customer=stripe_customer_id,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': user_id}
        )
        return JsonResponse({'checkout_url': session.url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)