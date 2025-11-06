import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .base import PaymentGateway
from ..services.services_abacate import norm_response
from decimal import Decimal, ROUND_HALF_UP
from server.settings import BASE_URL, ABACATE_API_TEST_KEY
from usuario.models import CustomUser
import requests

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
    
    def create_payment(
        self,
        amount: float,
        items: list,
        currency: str = "BRL",
        metadata: Optional[Dict[str, Any]] = None,
        allow_coupons: bool = False,
        coupons: Optional[list] = None
    ) -> Dict[str, Any]:
        try:
            return_url = BASE_URL
            completion_url = BASE_URL
            coupons = coupons or []
            # Monta lista de produtos convertendo preço para centavos
            products_payload = []
            user_id = metadata.get("user_id") if metadata else "unknown_user"
            user_obj = CustomUser.objects.get(id=user_id)
            user_hash = str(user_obj.hash_id)
            user_name = user_obj.get_full_name() or user_obj.username
            user_email = user_obj.email
            for prod in items:
                price_cents = int((Decimal(str(prod["price"])) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                products_payload.append({
                    "externalId": f"prod-{prod["id"]}",
                    "name": prod["name"],
                    "quantity": prod.get("quantity", 1),
                    "price": price_cents
                })
            payload = {
                "frequency": "ONE_TIME",
                "methods": ["PIX"],
                "products": products_payload,
                "returnUrl": return_url,
                "completionUrl": completion_url,
                "allowCoupons": allow_coupons,
                "coupons": coupons,
            }
            # logger.info(f"Criando pagamento AbacatePay com payload: {payload}")
            # result = self.client.billing.create(payload)
            # logger.info(f"AbacatePay raw result: {type(result)}")
            # gateway_response = norm_response(result)
            # logger.info(f"AbacatePay normalized response: {gateway_response}")
            
            
            response = requests.post(
                "https://api.abacatepay.com/v1/billing/create",
                json=payload,
                headers={
                    "Authorization": f"Bearer {ABACATE_API_TEST_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            logger.info(f"Resposta da API AbacatePay: {response.status_code} - {response.text}")
            response.raise_for_status()
            api_response = response.json()
            gateway_response = api_response
            
            faturamento = gateway_response.get("faturamento", {})
            valores = gateway_response.get("valores", {})
            data = gateway_response.get("data", {})
            url = data.get("url", "")

            payload_retorno = {
                "id": faturamento.get("id"),
                "status": "pending",  # Status inicial sempre pendente até pagamento
                "amount": valores.get("total"),
                "currency": 'BRL',
                "init_point": url,  # URL para redirecionar o usuário
                "gateway_response": gateway_response,
                "simulated": False
            }
            return payload_retorno
        except Exception as e:
            logger.error(f"Error creating AbacatePay payment: {type(e).__name__}: {e}", exc_info=True)
            raise
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Verifica o status de um pagamento"""
        try:
            result = None
            transaction_id = getattr(self.client, 'transactionId', None)
            
            if hasattr(transaction_id, 'check'):
                result = transaction_id.check(transaction_id)
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
