import stripe
from ..models import Payment
from .payment_service import PaymentService
from usuario.models import CustomUser
from datetime import datetime
from typing import Optional
from django.db.models import Q
import logging
import requests
from server.settings import MERCADOPAGO_ACCESS_TOKEN


def _ensure_datetime(value) -> Optional[datetime]:
    """Converte vários formatos em datetime ou retorna None.

    Aceita: datetime, int/float timestamp, numeric string, ISO datetime string.
    """
    if isinstance(value, datetime):
        return value
    # números (timestamp)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(int(value))
        except Exception:
            return None
    # strings: pode ser timestamp numérico ou ISO
    if isinstance(value, str):
        try:
            return datetime.fromtimestamp(int(value))
        except Exception:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
    return None


def processing_payment(transaction_id: str, user_email: str) -> bool:
    try:
        payment_obj = Payment.objects.get(transaction_id=transaction_id, user__email=user_email)
    except Payment.DoesNotExist:
        return False

    if payment_obj.status == "completed":
        return True

    payment_obj.status = "completed"
    PaymentService._finalize_payment(payment_obj)
    payment_obj.save()
    return True

def handle_checkout_session_completed(event_data: dict) -> bool:
    session = event_data.get('object', {})
    metadata = session.get('metadata', {})
    transaction_id = metadata.get('transaction_id')
    user_email = session.get('customer_email')
    mode = session.get('mode')
    status = session.get('payment_status')
    if status == 'paid':
        if mode == "payment":
            return processing_payment(transaction_id, user_email)

        elif mode == "subscription":
            print(f"WEBHOOK: Ainda não processamos subscription por aqui, {user_email}, transação {transaction_id}.")
            return True
    else:
        print(f"SERVICE: Checkout Session com status de pagamento '{status}' não processado.")
        return False

def handle_invoice_paid(event_data):
    invoice = event_data['object']
    subscription = event_data['object']
    customer_id = subscription.get('customer')

    try:
        dt_expiracao = get_invoice_period_end_datetime(subscription)
        if not dt_expiracao:
            print(f"SERVICE: Não foi possível obter o período de fim da fatura para o cliente {customer_id}.")
            return

        return update_vip_status(customer_id, dt_expiracao)
    except CustomUser.DoesNotExist:
        print(f"SERVICE: Usuário com ID {customer_id} não encontrado.")
    except Exception as e:
        print(f"SERVICE: Erro ao atualizar VIP do usuário: {e}")

def handle_invoice_payment_failed(event_data):
    invoice = event_data['object']
    customer_id = invoice.get('customer')
    pass

def handle_subscription_updated(event_data):
    print("SERVICE: Assinatura Atualizada.")
    subscription = event_data['object']
    customer_id = subscription.get('customer')
    
    dt_expiracao = get_subscription_current_period_end_datetime(subscription)
    if not dt_expiracao:
        print(f"SERVICE: Não foi possível obter o período de fim da fatura para o e-mail {customer_id}.")
        return
    return update_vip_status(customer_id, dt_expiracao)

    

def handle_subscription_deleted(event_data):
    subscription = event_data['object']
    customer_id = subscription.get('customer')
    pass

def handle_unmanaged_event(event_data):
    # tenta obter o tipo de evento de forma robusta: dicionário, objeto com atributo 'type', ou None
    event_type = None
    try:
        if isinstance(event_data, dict):
            event_type = event_data.get('type', None)
        else:
            event_type = getattr(event_data, 'type', None)
    except Exception:
        event_type = None

    if event_type is None:
        # mostrar informação útil para debugging: se é None, ou qual é o tipo do objeto recebido
        if event_data is None:
            data_repr = 'NoneType'
        else:
            try:
                data_repr = f"{type(event_data).__name__}: {repr(event_data)}"
            except Exception:
                data_repr = f"{type(event_data).__name__}"
        print(f"SERVICE: Evento sem 'type' ({data_repr}) recebido, não gerenciado.")
    else:
        print(f"SERVICE: Evento '{event_type}' recebido, mas não gerenciado.")
    return False

def get_invoice_period_end_datetime(invoice: dict) -> Optional[datetime]:
    lines = invoice.get('lines', {}).get('data', [])
    if not isinstance(lines, list) or not lines:
        return None

    first = lines[0]
    if not isinstance(first, dict):
        return None

    period = first.get('period')
    if not isinstance(period, dict):
        return None

    end_ts = period.get('end')
    if end_ts is None:
        return None

    # aceitar timestamps numéricos ou objetos datetime/strings ISO
    return _ensure_datetime(end_ts)

def get_subscription_current_period_end_datetime(subscription: dict) -> Optional[datetime]:
    items = subscription.get('items', {}).get('data', [])
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            current_end = first.get('current_period_end')
            if current_end is not None:
                dt = _ensure_datetime(current_end)
                if dt:
                    return dt

    sub_current_end = subscription.get('current_period_end')
    if sub_current_end is not None:
        dt = _ensure_datetime(sub_current_end)
        if dt:
            return dt

    return None


def update_vip_status(customer_id, dt_expiracao: datetime) -> bool:
    print(f"SERVICE: Atualizando VIP para o cliente {customer_id} até {dt_expiracao}.")
    customer = stripe.Customer.retrieve(customer_id)
    customer_email = customer.get('email')
    try:
        usuario = CustomUser.objects.get(email=customer_email)
    except CustomUser.DoesNotExist:
        print(f"SERVICE: User with email {customer_email} not found.")
        return False

    # Normaliza dt_expiracao para datetime
    dt = _ensure_datetime(dt_expiracao) if dt_expiracao is not None else None
    if not dt:
        print(f"SERVICE: Data de expiração inválida para cliente {customer_id}: {dt_expiracao}")
        return False

    # vip_expiration é um DateField; armazenar apenas a data
    usuario.vip_expiration = dt.date()
    usuario.is_vip = True
    # salvar
    usuario.save()
    print(f"SERVICE: VIP status updated for {usuario.username} until {usuario.vip_expiration}.")
    return True


def process_mercadopago_event(data: dict):
    """Processa payload de webhook do MercadoPago.

    Retorna (status_code, response_dict) para uso direto na view.
    Mantém comportamento compatível com a implementação anterior em views_webhook.py.
    """
    logger = logging.getLogger(__name__)
    # Validar formato básico
    action = (data.get('action') or '')
    type_field = data.get('type') or ''
    topic = data.get('topic') or ''

    # Ignorar eventos que não sejam de pagamento
    if action and not action.startswith('payment') and type_field != 'payment' and topic != 'payment':
        logger.info("MercadoPago webhook (não-pagamento) recebido: action=%s topic=%s type=%s", action, topic, type_field)
        return 200, {"status": "ignored_non_payment_event", "action": action or topic or type_field}

    # Extrair payment_id de vários formatos possíveis
    payment_id = None
    if data.get('data') and isinstance(data.get('data'), dict):
        payment_id = data.get('data', {}).get('id')

    # Alguns webhooks usam 'resource' com URL
    if not payment_id:
        resource = data.get('resource')
        if isinstance(resource, str) and '/payments/' in resource:
            payment_id = resource.rstrip('/').split('/')[-1]

    if not payment_id:
        logger.error("Webhook MercadoPago: ID do pagamento ausente no payload")
        return 400, {"error": "missing_payment_id"}

    logger.info("Webhook MercadoPago recebido (service): payment_id=%s", payment_id)

    mp_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}"}
    try:
        resp = requests.get(mp_url, headers=headers, timeout=10)
        mp_data = resp.json()
    except Exception as e:
        logger.exception("Erro ao obter dados MP: %s", e)
        return 502, {"error": "mp_api_error"}

    if resp.status_code != 200:
        logger.error("MP API retornou %s: %s", resp.status_code, getattr(resp, 'text', ''))
        return 404, {"error": "mp_not_found"}

    metadata = mp_data.get('metadata') or {}
    tx_id = metadata.get('transaction_id')

    payment = Payment.objects.filter(
        Q(gateway_payment_id=str(payment_id)) | Q(transaction_id=tx_id),
        gateway='mercadopago'
    ).first()

    if not payment:
        logger.warning("Pagamento não encontrado para mp_id=%s tx=%s", payment_id, tx_id)
        return 404, {"error": "payment_not_found"}

    # Comparar valores apenas logando discrepâncias
    mp_amount = mp_data.get('transaction_amount')
    try:
        if mp_amount is not None and float(mp_amount) != float(payment.amount):
            logger.warning("Valor divergente para payment %s: mp=%s db=%s", payment.transaction_id, mp_amount, payment.amount)
    except Exception:
        pass

    # Salvar o id do pagamento do gateway (se vier) para facilitar identificação futura
    mp_payment_id = mp_data.get('id') or mp_data.get('collection_id') or mp_data.get('payment_id')
    try:
        if mp_payment_id and (not payment.gateway_payment_id or str(payment.gateway_payment_id) != str(mp_payment_id)):
            payment.gateway_payment_id = str(mp_payment_id)
    except Exception:
        logger.exception("Falha ao atribuir gateway_payment_id para payment %s", getattr(payment, 'transaction_id', 'unknown'))

    # sempre atualiza gateway_response com os dados frescos
    payment.gateway_response = mp_data
    payment.save()

    # Delegar lógica de verificação/atualização de status ao PaymentService quando possível
    mp_status_raw = (mp_data.get('status') or '').lower()
    try:
        updated = PaymentService.check_payment_status(payment)
        if updated.status != 'completed' and mp_status_raw in ('approved', 'accredited', 'paid'):
            old_status = updated.status
            updated.status = 'completed'
            updated.save()
            try:
                PaymentService._finalize_payment(updated, old_status=old_status)
            except Exception:
                logger.exception("Erro ao finalizar pagamento após webhook MP (force finalize)")

        return 200, {"status": "success", "mp_status": mp_status_raw, "payment_status": updated.status}
    except Exception as e:
        # Se o PaymentService falhar por algum motivo (rede, erro), aplicamos fallback local
        logger.exception("PaymentService.check_payment_status falhou, aplicando fallback: %s", e)
        internal_status = PaymentService.STATUS_MAP.get(mp_status_raw) or {'approved': 'completed', 'accredited': 'completed'}.get(mp_status_raw)
        old_status = payment.status
        if internal_status:
            payment.status = internal_status
            payment.save()
        if payment.status == 'completed' and old_status != 'completed':
            try:
                PaymentService._finalize_payment(payment, old_status=old_status)
            except Exception:
                logger.exception("Erro ao finalizar pagamento após webhook MP (fallback)")
        return 200, {"status": "success", "mp_status": mp_status_raw, "payment_status": payment.status}