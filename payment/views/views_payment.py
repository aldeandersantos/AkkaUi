import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from ..models import Payment
from ..services.payment_service import PaymentService
from message.views import notify_discord

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def create_payment(request):
    """Cria um novo pagamento"""
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    gateway = data.get("gateway")
    plan = data.get("plan")
    
    if not gateway:
        return JsonResponse({"error": "missing_gateway"}, status=400)
    
    if not plan:
        return JsonResponse({"error": "missing_plan"}, status=400)
    
    # Validar gateway suportado
    if gateway not in PaymentService.GATEWAY_MAP:
        return JsonResponse({
            "error": "unsupported_gateway"
        }, status=400)
    
    # Validar plano
    if plan not in PaymentService.PLAN_PRICES:
        return JsonResponse({
            "error": "invalid_plan"
        }, status=400)
    
    try:
        payment = PaymentService.create_payment(
            user=request.user,
            gateway_name=gateway,
            plan=plan,
            currency=data.get("currency", "BRL")
        )
        notify_discord(request.user, "generated_buy", payment.amount, "created")
        return JsonResponse({
            "status": "success",
            "payment": {
                "transaction_id": payment.transaction_id,
                "gateway": payment.gateway,
                "plan": payment.plan,
                "amount": f"{payment.amount:.2f}",
                "currency": payment.currency,
                "status": payment.status,
                "gateway_payment_id": payment.gateway_payment_id,
                "gateway_response": payment.gateway_response,
                "created_at": payment.created_at.isoformat(),
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating payment for user {request.user.username}: {type(e).__name__}: {e}", exc_info=True)
        
        # Em modo DEBUG, fornecer mais detalhes do erro
        from django.conf import settings
        error_detail = str(e) if settings.DEBUG else "Failed to create payment"
        
        return JsonResponse({
            "status": "error",
            "error": error_detail
        }, status=500)


@csrf_exempt
@login_required
def check_payment_status_view(request):
    """Verifica o status de um pagamento"""
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    transaction_id = data.get("transaction_id")
    
    if not transaction_id:
        return JsonResponse({"error": "missing_transaction_id"}, status=400)
    
    try:
        payment = Payment.objects.get(
            transaction_id=transaction_id,
            user=request.user
        )
    except Payment.DoesNotExist:
        return JsonResponse({"error": "payment_not_found"}, status=404)
    
    try:
        payment = PaymentService.check_payment_status(payment)
        
        return JsonResponse({
            "status": "success",
            "payment": {
                "transaction_id": payment.transaction_id,
                "gateway": payment.gateway,
                "plan": payment.plan,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "gateway_payment_id": payment.gateway_payment_id,
                "gateway_response": payment.gateway_response,
                "created_at": payment.created_at.isoformat(),
                "updated_at": payment.updated_at.isoformat(),
                "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
            }
        })
        
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return JsonResponse({
            "status": "error",
            "error": "Failed to check payment status"
        }, status=500)


@csrf_exempt
@login_required
def simulate_payment_view(request):
    """Simula a confirmação de um pagamento (apenas para testes)"""
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    transaction_id = data.get("transaction_id")
    
    if not transaction_id:
        return JsonResponse({"error": "missing_transaction_id"}, status=400)
    
    try:
        payment = Payment.objects.get(
            transaction_id=transaction_id,
            user=request.user
        )
    except Payment.DoesNotExist:
        return JsonResponse({"error": "payment_not_found"}, status=404)
    
    try:
        payment = PaymentService.simulate_payment_confirmation(payment)
        
        return JsonResponse({
            "status": "success",
            "payment": {
                "transaction_id": payment.transaction_id,
                "gateway": payment.gateway,
                "plan": payment.plan,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
            },
            "message": "Payment confirmed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error simulating payment: {e}")
        return JsonResponse({
            "status": "error",
            "error": "Failed to simulate payment"
        }, status=500)


@login_required
def list_user_payments(request):
    """Lista todos os pagamentos do usuário"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    return JsonResponse({
        "status": "success",
        "payments": [
            {
                "transaction_id": p.transaction_id,
                "gateway": p.gateway,
                "plan": p.plan,
                "amount": str(p.amount),
                "currency": p.currency,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in payments
        ]
    })
