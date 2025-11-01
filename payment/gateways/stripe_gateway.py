import logging
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
        
        Para compras únicas, usa o Payment Intents API
        """
        logger.info(f"Creating Stripe payment: {amount} {currency}")
        
        try:
            # Criar Payment Intent para pagamento único
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe usa centavos
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            return {
                "id": payment_intent.id,
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "client_secret": payment_intent.client_secret,
                "payment_url": f"https://checkout.stripe.com/pay/{payment_intent.client_secret}",
            }
            
        except stripe.error.StripeError as e:
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
            
        except stripe.error.StripeError as e:
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
            
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao simular confirmação no Stripe: {e}")
            return {
                "id": payment_id,
                "status": "failed",
                "error": str(e)
            }
