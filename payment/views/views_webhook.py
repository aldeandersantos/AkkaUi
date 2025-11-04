import json
import logging
import hmac
import hashlib
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.dispatch import receiver
from django.conf import settings
from ..models import Payment
from django.db.models import Q
from ..services.payment_service import PaymentService
from djstripe.signals import WEBHOOK_SIGNALS
from djstripe import signals as djstripe_signals
from usuario.views.views_vip import add_vip_to_user_by_hash
from server.settings import MERCADOPAGO_ACCESS_TOKEN

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def abacatepay_webhook(request):
    """
    Webhook para receber notificações do AbacatePay quando um pagamento for confirmado.
    
    O AbacatePay envia uma notificação POST quando o status do pagamento muda.
    Esperamos um payload JSON com pelo menos: {"id": "payment_id", "status": "confirmed"}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Webhook AbacatePay: JSON inválido")
        return JsonResponse({"error": "invalid_json"}, status=400)

    payload = data.get("data")
    pix = payload.get("pixQrCode")
    payment_info = payload.get("payment")

    payment_id = pix.get("id")
    status = pix.get("status")
    payment_amount = pix.get("amount")
    amount_paid = payment_info.get("amount")
    
    if amount_paid != payment_amount:
        logger.warning(f"Webhook AbacatePay: Aviso de valor divergente - amount: {payment_amount}, amount_paid: {amount_paid}")
    
    if not payment_id:
        logger.error("Webhook AbacatePay: ID do pagamento ausente")
        return JsonResponse({"error": "missing_payment_id"}, status=400)

    logger.info(f"Webhook AbacatePay recebido: payment_id={payment_id}, status={status}")

    try:
        # Buscar o pagamento no banco pelo gateway_payment_id
        payment = Payment.objects.filter(
            gateway_payment_id=payment_id,
            gateway='abacatepay'
        ).first()

        if not payment:
            logger.warning(f"Webhook AbacatePay: Pagamento não encontrado para ID {payment_id}")
            return JsonResponse({"error": "payment_not_found"}, status=404)

        # Atualizar o status do pagamento
        old_status = payment.status
        # payment.plan armazena o value das choices (ex: 'pro_month' ou 'pro_year')
        plan = payment.plan
        # Se o status for "confirmed" ou "paid", marcar como completado
        status = status.lower()
        if status in ['confirmed', 'paid', 'completed']:
            payment = PaymentService.check_payment_status(payment)
            logger.info(f"Pagamento {payment_id} atualizado: {old_status} -> {payment.status}")

            if payment.status == 'completed' and old_status != 'completed':
                logger.info(f"Pagamento {payment_id} completado — VIP aplicado por PaymentService para usuário {payment.user.username}")
        else:
            # Para outros status, apenas atualizar
            payment.gateway_response = data
            payment.status = PaymentService.STATUS_MAP.get(status, payment.status)
            payment.save()
            logger.info(f"Status do pagamento {payment_id} atualizado para {payment.status}")

        return JsonResponse({
            "status": "success",
            "message": "Webhook processado com sucesso",
            "payment_status": payment.status
        })

    except Exception as e:
        logger.error(f"Erro ao processar webhook AbacatePay: {e}", exc_info=True)
        return JsonResponse({"error": "internal_error"}, status=500)


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    """
    Webhook para receber notificações do Mercado Pago.

    Recebe payload com: {"action": "payment.created", "data": {"id": "..."}, ...}
    Busca o detalhe do pagamento usando o `MERCADOPAGO_ACCESS_TOKEN` e atualiza o Payment local.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Webhook MercadoPago: JSON inválido")
        return JsonResponse({"error": "invalid_json"}, status=400)

    # Extrair payment id enviado no webhook
    payment_id = None
    try:
        payment_id = data.get('data', {}).get('id')
    except Exception:
        payment_id = None

    if not payment_id:
        logger.error("Webhook MercadoPago: ID do pagamento ausente")
        return JsonResponse({"error": "missing_payment_id"}, status=400)

    logger.info(f"Webhook MercadoPago recebido: payment_id={payment_id}")

    # Obter token do settings
    token = MERCADOPAGO_ACCESS_TOKEN
    if not token:
        logger.error("MERCADOPAGO_ACCESS_TOKEN não configurado nas settings")
        return JsonResponse({"error": "mp_token_missing"}, status=500)

    # Chamar API do Mercado Pago para obter detalhes do pagamento
    mp_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(mp_url, headers=headers, timeout=10)
    except Exception as e:
        logger.exception("Erro ao consultar API MercadoPago: %s", e)
        return JsonResponse({"error": "mp_api_error"}, status=502)

    if resp.status_code != 200:
        logger.error(f"MP API retornou {resp.status_code}: {resp.text}")
        return JsonResponse({"error": "mp_not_found", "status_code": resp.status_code}, status=404)

    try:
        mp_data = resp.json()
    except Exception as e:
        logger.exception("Resposta MP não é JSON: %s", e)
        return JsonResponse({"error": "invalid_mp_response"}, status=502)

    # Tentar relacionar ao Payment local
    metadata = mp_data.get('metadata', {}) or {}
    tx_id = metadata.get('transaction_id')

    payment = Payment.objects.filter(
        Q(gateway_payment_id=str(payment_id)) | Q(transaction_id=tx_id),
        gateway='mercadopago'
    ).first()

    if not payment:
        logger.warning(f"Webhook MercadoPago: Pagamento não encontrado para mp_id={payment_id} tx={tx_id}")
        # Retornar 404 para que possamos investigar; não é erro interno
        return JsonResponse({"error": "payment_not_found"}, status=404)

    # Comparar valores (só logar discrepâncias)
    try:
        mp_amount = mp_data.get('transaction_amount')
        if mp_amount is not None and float(mp_amount) != float(payment.amount):
            logger.warning(
                "Webhook MercadoPago: Valor divergente para payment %s: mp=%s db=%s",
                payment.transaction_id, mp_amount, payment.amount
            )
    except Exception:
        logger.debug("Não foi possível comparar valores de transação (formatos inesperados)")

    # Mapear status do MP para status interno
    mp_status_raw = (mp_data.get('status') or '').lower()
    # Usar o mapa do PaymentService quando possível, acrescentando 'approved' e 'accredited'
    map_extra = {
        'approved': 'completed',
        'accredited': 'completed',
    }
    internal_status = PaymentService.STATUS_MAP.get(mp_status_raw) or map_extra.get(mp_status_raw)

    old_status = payment.status
    # Atualizar registro
    payment.gateway_response = mp_data
    if internal_status:
        payment.status = internal_status
    else:
        # Se não sabemos, manter o status atual e apenas salvar a resposta
        logger.info(f"Status MP desconhecido '{mp_status_raw}' - mantendo status atual '{payment.status}'")

    payment.save()

    # Se passou para completed agora, executar finalização (evita chamar gateway novamente)
    try:
        if payment.status == 'completed' and old_status != 'completed':
            logger.info(f"Pagamento {payment_id} completado — iniciando finalização para user {payment.user.username}")
            PaymentService._finalize_payment(payment, old_status=old_status)
    except Exception as e:
        logger.exception("Erro ao finalizar pagamento após webhook MP: %s", e)

    return JsonResponse({
        "status": "success",
        "message": "Webhook MercadoPago processado com sucesso",
        "mp_status": mp_status_raw,
        "payment_status": payment.status
    })


@receiver(WEBHOOK_SIGNALS["checkout.session.completed"])
def handle_checkout_success(sender, event=None, **kwargs):
    """
    Esta função é acionada *apenas* quando o evento 
    'checkout.session.completed' é recebido.
    
    Não precisamos mais verificar o 'event.type' aqui dentro!
    """
    
    logger.info("Webhook 'checkout.session.completed' recebido do Stripe")

    try:
        # 'event' é o objeto do evento vindo do Stripe
        data = event.data
        # objeto da sessão
        obj = None
        try:
            obj = data.get('object') if isinstance(data, dict) else getattr(data, 'object', None)
        except Exception:
            obj = getattr(data, 'object', None)

        # Extrair campos importantes com tolerância a dict/obj
        def _get(o, key, default=None):
            try:
                if o is None:
                    return default
                if isinstance(o, dict):
                    return o.get(key, default)
                return getattr(o, key, default)
            except Exception:
                return default

        session_id = _get(obj, 'id')
        customer_email = _get(_get(obj, 'customer_details'), 'email')
        metadata = _get(obj, 'metadata') or {}

        logger.info(f"Stripe session_id={session_id} customer_email={customer_email}")

        # Tentar localizar Payment pelo gateway_payment_id (mais direto)
        payment = None
        if session_id:
            payment = Payment.objects.filter(gateway='stripe', gateway_payment_id=session_id).first()

        # Se não achou, tentar pelo transaction_id passado em metadata
        tx_id = None
        try:
            if isinstance(metadata, dict):
                tx_id = metadata.get('transaction_id')
        except Exception:
            tx_id = None

        if not payment and tx_id:
            payment = Payment.objects.filter(transaction_id=tx_id, gateway='stripe').first()

        # Como último recurso, tentar achar pelo email do usuário (o mais frágil)
        if not payment and customer_email:
            payment = Payment.objects.filter(user__email=customer_email, gateway='stripe').order_by('-created_at').first()

        if not payment:
            logger.warning(f"Webhook Stripe: Payment não encontrado para session {session_id} tx={tx_id} email={customer_email}")
            return

        old_status = payment.status

        # Atualizar status usando PaymentService para manter consistência
        try:
            payment = PaymentService.check_payment_status(payment)
            logger.info(f"Pagamento {payment.transaction_id} atualizado via webhook: {old_status} -> {payment.status}")

            if payment.status == 'completed' and old_status != 'completed':
                logger.info(f"Pagamento {payment.transaction_id} completado via webhook — finalizando para user {payment.user.username}")
        except Exception as e:
            logger.exception("Erro ao atualizar status do pagamento via PaymentService: %s", e)

    except Exception as e:
        logger.exception(f"Erro ao processar o webhook checkout.session.completed: {e}")


# Compat layer: dj-stripe may send a generic webhook_post_process signal with
# kwargs (instance, api_key). Algumas versões/integrations chamam receivers
# que esperam um parâmetro `event`; para evitar TypeError, registremos um
# receiver genérico que aceita os kwargs e delega para nossa função específica.
@receiver(djstripe_signals.webhook_post_process)
def handle_stripe_webhook(sender, instance=None, api_key=None, **kwargs):
    """Receiver genérico que injeta `event` para handlers que esperam esse nome.

    Quando dj-stripe processa um webhook, ele envia `webhook_post_process` com
    `instance` contendo o payload/objeto do evento. Aqui detectamos o tipo e
    delegamos para `handle_checkout_success` quando apropriado.
    """
    try:
        event_obj = instance or kwargs.get('event')

        # Tentar extrair o tipo do evento de forma robusta
        ev_type = None
        if isinstance(event_obj, dict):
            ev_type = event_obj.get('type')
        else:
            ev_type = getattr(event_obj, 'type', None) or getattr(event_obj, 'event_type', None)

        if ev_type == 'checkout.session.completed':
            try:
                # Delegar para o handler existente que espera o kwarg `event`
                handle_checkout_success(sender, event=event_obj)
            except Exception as e:
                logger.exception('Erro ao delegar checkout.session.completed: %s', e)
        else:
            logger.debug('Webhook dj-stripe recebido tipo=%s — sem handler específico', ev_type)
    except Exception as e:
        logger.exception('Erro no receiver genérico de webhooks dj-stripe: %s', e)
