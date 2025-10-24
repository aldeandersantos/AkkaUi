import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..models import Payment
from ..services.payment_service import PaymentService
from usuario.views.views_vip import add_vip_to_user_by_hash

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
                logger.info(f"VIP ativado para usuário {payment.user.username} via webhook AbacatePay")
                # Determina se é mensal ou anual e reaplica VIP usando função reutilizável
                try:
                    if plan == 'Pro Mensal':
                        success, msg = add_vip_to_user_by_hash(payment.user.hash_id, addition_type='month')
                    elif plan == 'Pro Anual':
                        success, msg = add_vip_to_user_by_hash(payment.user.hash_id, addition_type='year')
                    else:
                        success, msg = False, 'Plano não mapeado para VIP automático.'

                    if success:
                        logger.info(f"VIP atualizado para {payment.user.username}: {msg}")
                    else:
                        logger.warning(f"Não foi possível ativar VIP para {payment.user.username}: {msg}")
                except Exception as e:
                    logger.error(f"Erro ao ativar VIP via webhook para {payment.user.username}: {e}", exc_info=True)
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
