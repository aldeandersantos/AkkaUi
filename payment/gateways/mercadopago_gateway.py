import logging
import os
import uuid
from typing import Dict, Any, Optional, List
from django.conf import settings
from .base import PaymentGateway
from ..services.services_abacate import norm_response
from urllib.parse import urljoin
from server.settings import MERCADOPAGO_ACCESS_TOKEN

logger = logging.getLogger(__name__)


class MercadoPagoGateway(PaymentGateway):
    """Gateway de pagamento para Mercado Pago.

    Comportamento:
    - Se a biblioteca oficial do Mercado Pago estiver instalada e a variável
      de ambiente `MERCADOPAGO_ACCESS_TOKEN` estiver configurada, tenta usar
      o SDK para criar preferencias/pagamentos.
    - Caso contrário, opera em modo simulado (compatível com os stubs já
      presentes no projeto) para facilitar testes locais.
    """

    def __init__(self):
        # Ler configuração (usa a constante importada de server.settings quando disponível)
        # Prioriza `MERCADOPAGO_ACCESS_TOKEN` importado; caso esteja vazio, cai para settings
        self.access_token = MERCADOPAGO_ACCESS_TOKEN or getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", "")

        # Fallback direto para variáveis de ambiente caso settings não tenha sido populado
        if not self.access_token:
            self.access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN") or os.getenv("MERCADOPAGO_TOKEN_TEST") or os.getenv("MERCADOPAGO_TOKEN") or ""
            if self.access_token:
                logger.info("MercadoPago access token found via environment fallback")
            else:
                logger.debug("No MercadoPago access token found in settings or environment")
        self.client = None

        if self.access_token:
            try:
                import mercadopago

                # Inicializa o SDK do Mercado Pago
                self.client = mercadopago.SDK(self.access_token)
                logger.info("MercadoPago client initialized")
            except ImportError:
                logger.warning("mercadopago package not installed; using simulated mode")
            except Exception as e:
                logger.error(f"Error initializing MercadoPago client: {e}")

        if not self.client:
            logger.info("MercadoPago gateway initialized in simulated mode")

    def get_gateway_name(self) -> str:
        return "mercadopago"
    def create_payment(self, amount: float, currency: str = "BRL", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Cria uma preferência (preference) no Mercado Pago ou simula uma resposta."""
        metadata = metadata or {}
        logger.debug("Creating MercadoPago payment - amount=%s currency=%s metadata=%s", amount, currency, metadata)

        # Monta os items (preferência por metadata['items'] ou Payment.items quando disponível)
        items: List[Dict[str, Any]] = []
        if isinstance(metadata.get("items"), list) and metadata.get("items"):
            for it in metadata.get("items"):
                item = {
                    "id": it.get("id") or str(it.get("title", "item")),
                    "title": it.get("title", "Item"),
                    "quantity": int(it.get("quantity", 1)),
                    "currency_id": it.get("currency_id", currency),
                    "unit_price": float(it.get("unit_price", amount)),
                }
                if it.get("description"):
                    item["description"] = it.get("description")
                if it.get("picture_url"):
                    item["picture_url"] = it.get("picture_url")
                items.append(item)
        else:
            txid = metadata.get("transaction_id")
            if txid:
                try:
                    from ..models import Payment as PaymentModel

                    payment_obj = PaymentModel.objects.prefetch_related("items").get(transaction_id=txid)
                    for it in payment_obj.items.all():
                        items.append({
                            "id": str(it.item_id) or str(it.id),
                            "title": it.item_name or metadata.get("title", "Item"),
                            "quantity": int(it.quantity),
                            "currency_id": currency,
                            "unit_price": float(it.unit_price),
                        })
                except Exception as e:
                    logger.debug("Could not build items from Payment model for transaction %s: %s", txid, e)

            if not items:
                items = [
                    {
                        "id": metadata.get("transaction_id") or str(uuid.uuid4()),
                        "title": metadata.get("title", "Compra"),
                        "quantity": int(metadata.get("items_count", 1)),
                        "currency_id": currency,
                        "unit_price": float(amount),
                    }
                ]

        # back_urls mínimos (podem ser sobrescritos via settings)
        # Usa a URL do site configurada em settings ou nas variáveis de ambiente.
        base_site_url = (
            getattr(settings, "BASE_URL", "")).rstrip("/")

        if not base_site_url:
            base_site_url = "http://localhost:8000"
            logger.warning("BASE_URL não definido em settings/ambiente; usando fallback %s", base_site_url)

        back_urls_raw = {
            "success": urljoin(base_site_url + "/", "api/mercadopago/success/"),
            "pending": urljoin(base_site_url + "/", "api/mercadopago/pending/"),
            "failure": urljoin(base_site_url + "/", "api/mercadopago/failure/"),
        }

        # Filtra back_urls vazias e só inclui auto_return quando success estiver definido
        back_urls = {k: v for k, v in back_urls_raw.items() if v}

        auto_return_setting = getattr(settings, "MERCADOPAGO_AUTO_RETURN", None)
        pref_auto_return = None
        if auto_return_setting and back_urls.get("success"):
            pref_auto_return = auto_return_setting
        else:
            if auto_return_setting:
                logger.warning("MERCADOPAGO_AUTO_RETURN is set but no back_urls.success found; omitting auto_return to avoid API error")

        preference_data: Dict[str, Any] = {
            "items": items,
            "metadata": metadata or {},
        }

        if pref_auto_return:
            preference_data["auto_return"] = pref_auto_return

        if back_urls:
            preference_data["back_urls"] = back_urls

        preference_data["notification_url"] = urljoin(base_site_url + "/", "en/payment/webhook/abacatepay/")
        preference_data["notification_url"] = "https://webhook.site/b3c34617-5642-4486-911b-80459f75b040"
        preference_data["external_reference"] = metadata.get("transaction_id", str(uuid.uuid4()))
        #preference_data["auto_return"] = "all"

        # Se há client do SDK, usa-o para criar a preferência
        if self.client:
            try:
                result = self.client.preference().create(preference_data)
                response = result.get("response", result)
                try:
                    return norm_response(response)
                except Exception:
                    return response
            except Exception as e:
                logger.exception("Error creating MercadoPago preference: %s", e)
                return {"error": str(e)}

        # Modo simulado - retorna estrutura compatível para frontend (init_point)
        sim_id = f"sim-{uuid.uuid4()}"
        simulated = {
            "id": sim_id,
            "init_point": f"https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id={sim_id}",
            "sandbox_init_point": f"https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id={sim_id}",
            "items": items,
            "metadata": metadata or {},
        }
        logger.debug("MercadoPago gateway running in simulated mode - returning simulated preference %s", sim_id)
        return simulated
    
    def check_payment_status(self, gateway_payment_id: str) -> Dict[str, Any]:
        """Retorna o status do pagamento identificado por `gateway_payment_id`.

        - Se o SDK estiver disponível, consulta `payment().get(payment_id)`.
        - Caso contrário, retorna um status simulado.
        """
        if self.client:
            try:
                result = self.client.payment().get(gateway_payment_id)
                response = result.get("response", result)
                logger.debug("Payment status fetched: %s", response.get("status", "<no-status>"))
                return response
            except Exception as e:
                logger.exception("Error fetching payment status: %s", e)
                return {"error": str(e)}

        # Simulado
        logger.debug("check_payment_status: returning simulated status for %s", gateway_payment_id)
        return {"id": gateway_payment_id, "status": "simulated", "status_detail": "simulated_ok"}

    def simulate_payment_confirmation(self, payment_id: str) -> Dict[str, Any]:
        """Simula confirmação de pagamento (útil para testes locais sem SDK)."""
        logger.info("Simulating payment confirmation for %s", payment_id)
        return {"id": payment_id, "status": "approved", "simulated": True}