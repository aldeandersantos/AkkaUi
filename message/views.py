import logging
import requests
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from server.settings import (
    DISCORD_WEBHOOK_CONFIRMOU_PAGAMENTO,
    DISCORD_WEBHOOK_ADQUIRIU_ASSINATURA,
    DISCORD_WEBHOOK_GEROU_COMPRA,
    DISCORD_WEBHOOK_CRIOU_CONTA,
    DISCORD_WEBHOOK_ENTROU_PRECO,
)




def notify_discord(username: str, type: str, amount: float, status: str):
    if type == "vip":
        webhook_url = DISCORD_WEBHOOK_ADQUIRIU_ASSINATURA
        content = build_message_vip_buy(username, vip_months=amount)
    elif type == "generated_buy":
        webhook_url = DISCORD_WEBHOOK_GEROU_COMPRA
        content = build_message_generated_buy(username, amount)
    elif type == "confirmed_payment":
        webhook_url = DISCORD_WEBHOOK_CONFIRMOU_PAGAMENTO
        content = _build_payment_message(username, amount, status)
    _send_discord_webhook(webhook_url, content)


def _send_discord_webhook(webhook_url: str, content: str, timeout: int = 5) -> None:
    """Envio genérico para um webhook do Discord."""
    logger = logging.getLogger(__name__)
    if not webhook_url:
        logger.warning("Webhook do Discord não configurado")
        return

    payload = {"content": content}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        logger.exception("Falha ao enviar payload para webhook %s", webhook_url)


def _build_payment_message(username: str, amount: float, status: str):
    """Constrói o conteúdo da mensagem de pagamento."""
    status = status.capitalize()
    username = username.capitalize() or "Desconhecido"
    amount = Decimal(amount).quantize(Decimal("0.01"))
    content = (
        f"💳 **Pagamento Confirmado** 💳\n"
        f"👤 **Usuário:** {username}\n"
        f"💰 **Valor:** R${amount}\n"
        f"🔄 **Status:** {status}\n"
    )
    return content


def build_message_vip_buy(username: str, vip_months: int) -> str:
    meses = int(vip_months)
    unidade = "mês" if meses == 1 else "ano"
    content = (
        f"🎉 **VIP Adquirido** 🎉\n"
        f"👤 **Usuário:** {username}\n"
        f"✨ **Duração:** {meses} {unidade}\n\n"
    )
    return content

def build_message_generated_buy(username: str, amount: float) -> str:
    content = (
        f"🛒 **Compra Pendente** 🛒\n"
        f"👤 **Usuário:** {username}\n"
        f"💰 **Valor:** R${amount:.2f}\n\n"
        f"Uma nova compra foi gerada no sistema."
    )
    return content