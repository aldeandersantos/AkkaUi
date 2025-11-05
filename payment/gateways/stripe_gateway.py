import logging
import json
from typing import Dict, Any, Optional
from .base import PaymentGateway
from django.conf import settings
import stripe

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGateway):
    """Gateway de pagamento para Stripe - suporta compras únicas e assinaturas"""
    
    def __init__(self):
        # Configurar chave da API do Stripe
        stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY if settings.STRIPE_LIVE_MODE else settings.STRIPE_TEST_SECRET_KEY
        logger.info("Stripe gateway initialized")
    
    def get_gateway_name(self) -> str:
        return "stripe"
    
    def create_payment(self, amount: float, currency: str = "BRL", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cria um pagamento via Stripe (compra única)
        
        Usa Stripe Checkout Session para redirecionar o usuário
        """
        logger.info(f"Creating Stripe payment: {amount} {currency}")
        
        try:
            # Converter metadata complexo para strings (Stripe só aceita strings em metadata)
            stripe_metadata = {}
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (dict, list)):
                        # Converter objetos complexos para JSON string
                        stripe_metadata[key] = json.dumps(value)
                    else:
                        # Converter para string simples
                        stripe_metadata[key] = str(value)
            
            # Obter base URL para success/cancel
            base_url = getattr(settings, 'BASE_URL', None) or 'http://localhost:8000'
            base_url = base_url.rstrip('/')

            # Não usa mais prefixo de idioma nas URLs de sucesso/cancelamento
            success_url = f"{base_url}/success/?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base_url}/cancel/"
            
            # Criar Checkout Session para pagamento único
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'unit_amount': int(amount * 100),  # Stripe usa centavos
                        'product_data': {
                            'name': 'Pagamento AkkaUi',
                            'description': f"Valor: {currency} {amount:.2f}",
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=stripe_metadata,
            )
            
            return {
                "id": checkout_session.id,
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "init_point": checkout_session.url,  # URL para redirecionar o usuário
            }
            
        except stripe.StripeError as e:
            logger.error(f"Erro ao criar pagamento no Stripe: {e}")
            return {
                "id": None,
                "status": "failed",
                "amount": amount,
                "currency": currency,
                "error": str(e)
            }
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Verifica o status de um pagamento"""
        logger.info(f"Checking Stripe payment status: {payment_id}")
        
        try:
            # Tentar como Checkout Session primeiro
            try:
                checkout_session = stripe.checkout.Session.retrieve(payment_id)
                
                # Mapear status do Checkout Session
                status_map = {
                    'complete': 'completed',
                    'open': 'pending',
                    'expired': 'cancelled',
                }
                
                return {
                    "id": checkout_session.id,
                    "status": status_map.get(checkout_session.status, 'pending'),
                    "amount": checkout_session.amount_total / 100 if checkout_session.amount_total else 0,
                    "currency": checkout_session.currency.upper() if checkout_session.currency else 'BRL',
                }
            except:
                # Se falhar, tentar como Payment Intent (retrocompatibilidade)
                payment_intent = stripe.PaymentIntent.retrieve(payment_id)
                
                # Mapear status do Stripe para nosso sistema
                status_map = {
                    'succeeded': 'completed',
                    'processing': 'processing',
                    'requires_payment_method': 'pending',
                    'requires_confirmation': 'pending',
                    'requires_action': 'pending',
                    'canceled': 'cancelled',
                    'failed': 'failed',
                }
                
                return {
                    "id": payment_intent.id,
                    "status": status_map.get(payment_intent.status, 'pending'),
                    "amount": payment_intent.amount / 100,
                    "currency": payment_intent.currency.upper(),
                }
            
        except stripe.StripeError as e:
            logger.error(f"Erro ao verificar status no Stripe: {e}")
            return {
                "id": payment_id,
                "status": "failed",
                "error": str(e)
            }
    
    def simulate_payment_confirmation(self, payment_id: str) -> Dict[str, Any]:
        """Simula a confirmação de um pagamento (para testes)"""
        logger.info(f"Simulating Stripe payment confirmation: {payment_id}")
        
        # Em ambiente de teste, podemos confirmar o payment intent
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # No modo de teste, confirmar o pagamento
            if not settings.STRIPE_LIVE_MODE:
                if payment_intent.status in ['requires_payment_method', 'requires_confirmation']:
                    payment_intent = stripe.PaymentIntent.confirm(
                        payment_id,
                        payment_method='pm_card_visa',  # Cartão de teste
                    )
            
            return {
                "id": payment_intent.id,
                "status": "completed",
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency.upper(),
            }
            
        except stripe.StripeError as e:
            logger.error(f"Erro ao simular confirmação no Stripe: {e}")
            return {
                "id": payment_id,
                "status": "failed",
                "error": str(e)
            }
