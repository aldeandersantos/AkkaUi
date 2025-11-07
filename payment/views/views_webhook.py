import json
import logging
import stripe
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.dispatch import receiver
from django.conf import settings
from ..models import Payment
from django.db.models import Q
from ..services.payment_service import PaymentService
from ..services.stripe_service import stripe_signature_verification
from ..services.webhook_service import processing_stripe_payment
from usuario.views.views_vip import add_vip_to_user_by_hash
from server.settings import MERCADOPAGO_ACCESS_TOKEN, STRIPE_WEBHOOK_CHECKOUT, ABACATE_WEBHOOK_SECRET

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def abacatepay_webhook(request):
    """
    Webhook para receber notificações do AbacatePay quando um pagamento for confirmado.
    
    O AbacatePay envia uma notificação POST quando o status do pagamento muda.
    Esperamos um payload JSON com pelo menos: {"id": "payment_id", "status": "confirmed"}
    """
    secret_da_url = request.GET.get('webhookSecret') 

    if not secret_da_url or secret_da_url != ABACATE_WEBHOOK_SECRET:
        logger.error(f"Webhook AbacatePay: Tentativa de acesso não autorizada. Secret inválido.")
        return JsonResponse({"error": "unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Webhook AbacatePay: JSON inválido")
        return JsonResponse({"error": "invalid_json"}, status=400)
    payload = data.get("data")
    billing = payload.get("billing", {}) if payload else {}

    gateway_pay_id = billing.get("id")
    amount = billing.get("amount", 0)
    paid_amount = billing.get("paidAmount", 0)
    status = billing.get("status", "")

    if paid_amount != amount:
        logger.warning(f"Webhook AbacatePay: Aviso de valor divergente - amount: {amount}, paid_amount: {paid_amount}")
    amount = float(amount) / 100  # Usar o valor pago efetivamente

    if not gateway_pay_id:
        logger.error("Webhook AbacatePay: ID do pagamento ausente")
        return JsonResponse({"error": "missing_payment_id"}, status=400)

    logger.info(f"Webhook AbacatePay recebido: payment_id={gateway_pay_id}, status={status}")

    try:
        # Buscar o pagamento no banco pelo gateway_payment_id
        payment = Payment.objects.filter(
            gateway_payment_id=gateway_pay_id,
            gateway='abacatepay'
        ).first()

        if not payment:
            logger.warning(f"Webhook AbacatePay: Pagamento não encontrado para ID {gateway_pay_id}")
            return JsonResponse({"error": "payment_not_found"}, status=404)

        # Atualizar o status do pagamento
        old_status = payment.status
        # Se o status for "confirmed" ou "paid", marcar como completado
        status = status.lower()
        payment_id = payment.transaction_id
        if status == 'paid':
            logger.info(f"Pagamento {payment_id} atualizado: {old_status} -> {payment.status}")
            payment.status = 'completed'
            if old_status != 'completed':
                    try:
                        PaymentService._register_svg_purchases(payment)
                    except Exception as e:
                        logger.exception(f"Erro ao registrar compras de SVGs: {e}")
            payment.save()
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


@csrf_exempt
def stripe_webhook(request):
    try:
        payload = request.body
        data = json.loads(payload)
    except json.JSONDecodeError:
        logger.error("Webhook MercadoPago: JSON inválido")
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    sig_header = request.headers.get('Stripe-Signature')

    if not stripe_signature_verification(STRIPE_WEBHOOK_CHECKOUT, sig_header, payload):
        logger.warning("Webhook Stripe: Assinatura inválida")
        return JsonResponse({"error": "invalid_stripe_signature"}, status=403)


    if not sig_header:
        logger.error("Webhook Stripe: Header 'Stripe-Signature' ausente.")
        return HttpResponseBadRequest("Missing Stripe-Signature header")
    
    

    event_type = data.get("type", None)
    if event_type:
        session = "checkout.session."
        payment_status =  data.get("data", {}).get("object", {}).get("payment_status", None)

        if event_type == f"{session}completed":
            print(f"Processando evento {session}completed")
            if payment_status == "paid":
                print("Pagamento concluído com sucesso no Stripe.")
                if not processing_stripe_payment(data):
                    print("Falha ao processar o pagamento do Stripe.")

        elif event_type == f"{session}async_payment_succeeded":
            print(f"Processando evento {session}async_payment_succeeded")

        elif event_type == f"{session}async_payment_failed":
            print(f"Processando evento {session}async_payment_failed")

        elif event_type == f"{session}expired":
            print(f"Processando evento {session}expired")

        else:
            print(f"Evento Stripe não tratado: {event_type}")
    
    return HttpResponse(status=200)