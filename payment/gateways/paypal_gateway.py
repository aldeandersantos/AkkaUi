import logging
from typing import Dict, Any, Optional
from .base import PaymentGateway

logger = logging.getLogger(__name__)


class PayPalGateway(PaymentGateway):
    """Gateway de pagamento para PayPal (stub para implementação futura)"""
    
    def __init__(self):
        logger.info("PayPal gateway initialized (stub)")
    
    def get_gateway_name(self) -> str:
        return "paypal"
    
    def create_payment(self, amount: float, currency: str = "BRL", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Cria um pagamento via PayPal (simulado)"""
        logger.info(f"Creating PayPal payment: {amount} {currency}")
        
        return {
            "id": f"sim_paypal_{amount}",
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "payment_url": "https://www.paypal.com/checkoutnow?token=stub",
            "simulated": True,
            "message": "PayPal integration coming soon"
        }
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Verifica o status de um pagamento (simulado)"""
        logger.info(f"Checking PayPal payment status: {payment_id}")
        
        return {
            "id": payment_id,
            "status": "pending",
            "simulated": True,
            "message": "PayPal integration coming soon"
        }
    
    def simulate_payment_confirmation(self, payment_id: str) -> Dict[str, Any]:
        """Simula a confirmação de um pagamento (simulado)"""
        logger.info(f"Simulating PayPal payment confirmation: {payment_id}")
        
        return {
            "id": payment_id,
            "status": "completed",
            "simulated": True,
            "message": "PayPal integration coming soon"
        }
