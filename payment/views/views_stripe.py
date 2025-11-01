from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from djstripe.models import Price, Subscription
from payment.services.stripe_service import get_or_create_stripe_customer
from datetime import datetime
import stripe
import logging
import json

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def create_checkout_session(request):
    """
    Cria uma sessão de checkout do Stripe para assinatura.
    
    Espera JSON body:
    {
        "price_id": "price_xxx",  # ID do preço no Stripe
        "success_url": "http://example.com/success",
        "cancel_url": "http://example.com/cancel"
    }
    """
    try:
        data = json.loads(request.body)
        
        price_id = data.get('price_id')
        base_url = settings.BASE_URL or 'http://localhost:8000'
        success_url = data.get('success_url', f"{base_url}/payment/success/")
        cancel_url = data.get('cancel_url', f"{base_url}/payment/cancel/")
        
        if not price_id:
            return JsonResponse({'error': 'price_id é obrigatório'}, status=400)
        
        # Garante que o usuário tem um Customer no Stripe
        customer = get_or_create_stripe_customer(request.user)
        
        # Configura a API do Stripe
        stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY if settings.STRIPE_LIVE_MODE else settings.STRIPE_TEST_SECRET_KEY
        
        # Cria a sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': request.user.id,
                'user_email': request.user.email,
            }
        )
        
        return JsonResponse({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao criar checkout session: {e}", exc_info=True)
        return JsonResponse({'error': 'Erro ao criar sessão de checkout'}, status=500)


@login_required
@require_http_methods(["GET"])
def list_subscription_prices(request):
    """
    Lista os preços de assinatura disponíveis no Stripe.
    """
    try:
        # Busca preços ativos de assinaturas
        prices = Price.objects.filter(
            active=True,
            type='recurring'
        ).select_related('product')
        
        price_list = []
        for price in prices:
            price_data = {
                'id': price.id,
                'product': price.product.name if price.product else 'N/A',
                'amount': float(price.unit_amount / 100) if price.unit_amount else 0,
                'currency': price.currency,
                'interval': price.recurring.get('interval') if price.recurring else None,
                'interval_count': price.recurring.get('interval_count') if price.recurring else None,
            }
            price_list.append(price_data)
        
        return JsonResponse({'prices': price_list})
    
    except Exception as e:
        logger.error(f"Erro ao listar preços: {e}", exc_info=True)
        return JsonResponse({'error': 'Erro ao listar preços'}, status=500)


@login_required
@require_http_methods(["GET"])
def user_subscription_status(request):
    """
    Retorna o status da assinatura do usuário logado.
    """
    try:
        customer = get_or_create_stripe_customer(request.user)
        
        # Busca assinaturas do customer
        subscriptions = Subscription.objects.filter(
            customer=customer
        ).order_by('-created')
        
        subscription_list = []
        for sub in subscriptions:
            # Busca dados atualizados do Stripe
            try:
                stripe_sub = sub.api_retrieve()
                status = stripe_sub.get('status', 'unknown')
                current_period_end = stripe_sub.get('current_period_end')
                cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
            except Exception as e:
                logger.warning(f"Erro ao buscar dados da subscription {sub.id}: {e}")
                # Fallback para dados locais
                stripe_data = getattr(sub, 'stripe_data', {})
                status = stripe_data.get('status', 'unknown')
                current_period_end = stripe_data.get('current_period_end')
                cancel_at_period_end = stripe_data.get('cancel_at_period_end', False)
            
            subscription_list.append({
                'id': sub.id,
                'status': status,
                'current_period_end': datetime.fromtimestamp(current_period_end).isoformat() if current_period_end else None,
                'cancel_at_period_end': cancel_at_period_end,
            })
        
        return JsonResponse({
            'is_vip': request.user.is_vip,
            'vip_expiration': request.user.vip_expiration.isoformat() if request.user.vip_expiration else None,
            'subscriptions': subscription_list
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter status de assinatura: {e}", exc_info=True)
        return JsonResponse({'error': 'Erro ao obter status'}, status=500)


@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Endpoint para receber webhooks do Stripe.
    O dj-stripe já processa automaticamente, mas mantemos este endpoint
    para garantir compatibilidade.
    """
    # O dj-stripe já tem suas próprias views de webhook
    # Este endpoint pode ser usado como fallback ou para lógica customizada adicional
    return JsonResponse({'status': 'webhook recebido'})
