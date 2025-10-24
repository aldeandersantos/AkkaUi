import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .base import PaymentGateway
from ..services.services_abacate import norm_response
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class AbacatePayGateway(PaymentGateway):
    """Gateway de pagamento para Abacate Pay"""
    
    def __init__(self):
        self.api_key = getattr(settings, "ABACATE_API_TEST_KEY", "")
        self.client = None
        
        if self.api_key:
            try:
                from abacatepay import AbacatePay
                self.client = AbacatePay(api_key=self.api_key)
            except ImportError:
                logger.warning("abacatepay package not installed")
            except Exception as e:
                logger.error(f"Error initializing AbacatePay client: {e}")
    
    def get_gateway_name(self) -> str:
        return "abacatepay"
    
    def create_payment(self, amount: float, currency: str = "BRL", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Cria um pagamento PIX via Abacate Pay - compra real que fica pendente até pagamento"""
        if not self.client:
            # Modo simulado quando o cliente não está configurado
            logger.warning("AbacatePay client not configured. Using simulated mode.")
            return {
                "id": f"sim_abacate_{amount}",
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "qr_code": "simulated_qr_code_data",
                "qr_code_url": "https://example.com/qr-code-placeholder",
                "simulated": True
            }
        
        try:
            # Cria a compra real no AbacatePay - ficará pendente até o cliente pagar
            # Converte valor em reais para centavos (ex.: 9.9 -> 990)
            amount_dec = Decimal(str(amount))
            amount = int((amount_dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            logger.info(f"Valor convertido para centavos: {amount}")
            payload = {
                "amount": amount,
                "currency": currency,
            }
            
            if metadata:
                payload.update(metadata)
            
            logger.info(f"Creating AbacatePay payment with payload: {payload}")
            result = self.client.pixQrCode.create(payload)
            logger.info(f"AbacatePay raw result: {type(result)}")
            
            gateway_response = norm_response(result)
            logger.info(f"AbacatePay normalized response: {gateway_response}")
            
            return {
                "id": gateway_response.get("id"),
                "status": "pending",  # Status inicial sempre pendente até pagamento
                "amount": amount,
                "currency": currency,
                "qr_code": gateway_response.get("qr_code"),
                "qr_code_url": gateway_response.get("qr_code_url"),
                "gateway_response": gateway_response,
                "simulated": False
            }
        except Exception as e:
            logger.error(f"Error creating AbacatePay payment: {type(e).__name__}: {e}", exc_info=True)
            raise
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Verifica o status de um pagamento"""
        if not self.client:
            # Modo simulado
            return {
                "id": payment_id,
                "status": "pending",
                "simulated": True
            }
        
        try:
            result = None
            pix_client = getattr(self.client, 'pixQrCode', None)
            if pix_client is None:
                raise AttributeError("AbacatePay client has no attribute 'pixQrCode'")
            
            if hasattr(pix_client, 'check'):
                result = pix_client.check(payment_id)
            else:
                raise AttributeError("AbacatePay PixQrCode client does not implement 'check' method")

            gateway_response = norm_response(result)
            
            return {
                "id": payment_id,
                "status": gateway_response.get("status", "pending"),
                "gateway_response": gateway_response,
                "simulated": False
            }
        except Exception as e:
            logger.error(f"Error checking AbacatePay payment status: {e}")
            raise
    
    def simulate_payment_confirmation(self, payment_id: str) -> Dict[str, Any]:
        """Simula a confirmação de um pagamento PIX"""
        if not self.client:
            # Modo simulado
            return {
                "id": payment_id,
                "status": "completed",
                "simulated": True
            }
        
        try:
            result = self.client.pixQrCode.simulate(id=payment_id)
            gateway_response = norm_response(result)
            
            return {
                "id": payment_id,
                "status": "completed",
                "gateway_response": gateway_response,
                "simulated": False
            }
        except Exception as e:
            logger.error(f"Error simulating AbacatePay payment: {e}")
            raise
