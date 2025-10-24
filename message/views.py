import logging
import requests
from typing import Optional, Dict, Any



def notify_discord(payment_id: str, status: str, gateway_response: Optional[Dict[str, Any]] = None) -> None:
    """Envia notificação ao Discord informando confirmação de pagamento."""

    logger = logging.getLogger(__name__)
    DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1430966923213930578/C38b2CVQ3iFfqiYobjfnFMkcU8oAJS1ougqC72gY-tA4PtIfuD1F6oDfubwR4hPJ01UA"

    content_lines = [
        "Pagamento confirmado ✅",
        f"ID: {payment_id}",
        f"Status: {status}",
    ]

    if gateway_response and isinstance(gateway_response, dict):
        amount = gateway_response.get("amount")
        currency = gateway_response.get("currency")
        if amount is not None:
            from decimal import Decimal
            inteiro = Decimal(amount/100).quantize(Decimal("0.01"))
            content_lines.append(f"Valor: R${inteiro} {currency or ''}".strip())
        tx_id = gateway_response.get("id")
        if tx_id and tx_id != payment_id:
            content_lines.append(f"TX: {tx_id}")

    payload = {"content": "\n".join(content_lines)}

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Falha ao enviar notificação para o Discord: %s", exc)
