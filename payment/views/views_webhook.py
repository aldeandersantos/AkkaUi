import json
import logging
import requests
import stripe
from usuario.models import CustomUser
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
from ..services.webhook_service import *
from usuario.views.views_vip import add_vip_to_user_by_hash
from server.settings import MERCADOPAGO_ACCESS_TOKEN, STRIPE_WEBHOOK_CHECKOUT, ABACATE_WEBHOOK_SECRET
from datetime import datetime

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
def mercadopago_webhook_test(request):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nome_arquivo = f"mercadopago_webhook_{timestamp}.json"
    with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
        # Salva os headers como dict JSON
        headers_dict = dict(request.headers)
        arquivo.write(json.dumps({"headers": headers_dict}, ensure_ascii=False, indent=2))
        arquivo.write("\n")
        # Salva o body como JSON se possível, senão como texto
        try:
            body_json = json.loads(request.body)
            arquivo.write(json.dumps({"body": body_json}, ensure_ascii=False, indent=2))
        except Exception:
            arquivo.write(json.dumps({"body": request.body.decode("utf-8")}, ensure_ascii=False, indent=2))
        arquivo.write("\n-----\n")

@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    """
    Webhook para receber notificações do Mercado Pago.

    Recebe payload com: {"action": "payment.created", "data": {"id": "..."}, ...}
    Busca o detalhe do pagamento usando o `MERCADOPAGO_ACCESS_TOKEN` e atualiza o Payment local.
    """
    # Delegate processing to service to reduce duplication and keep view leve
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Webhook MercadoPago: JSON inválido")
        return JsonResponse({"error": "invalid_json"}, status=400)

    # process_mercadopago_event retorna (status_code, payload)
    try:
        status_code, payload = process_mercadopago_event(data)
    except Exception as e:
        logger.exception("Erro inesperado ao processar webhook MP: %s", e)
        return JsonResponse({"error": "internal_error"}, status=500)

    return JsonResponse(payload, status=status_code)


EVENT_HANDLER_MAP = {
    # Cliente se inscreveu
    'checkout.session.completed': handle_checkout_session_completed,
    # Renovação paga
    'invoice.paid': handle_invoice_paid,
    # Renovação falhou
    'invoice.payment_failed': handle_invoice_payment_failed,
    # Cliente mudou o plano ou agendou cancelamento
    'customer.subscription.updated': handle_subscription_updated,
    # Assinatura efetivamente cancelada (acesso removido)
    'customer.subscription.deleted': handle_subscription_deleted,
}


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_CHECKOUT
        )
    except ValueError as e:
        print(f"WEBHOOK ERRO: Payload inválido. {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"WEBHOOK ERRO: Assinatura inválida. {e}")
        return HttpResponse(status=400)

    event_type = event['type']
    event_data = event['data']

    handler = EVENT_HANDLER_MAP.get(
        event_type, 
        handle_unmanaged_event
    )

    try:
        handler(event_data)
    except Exception as e:
        print(f"ERRO NO HANDLER: Falha ao processar {event_type}: {e}")

    print("DEBUG: Finalizando processamento do webhook Stripe")
    return HttpResponse(status=200)
