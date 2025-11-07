import json
import logging
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from ..views.views_stripe import get_stripe_payment_data
from ..views.views_abacate import get_abacate_payment_data
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from ..models import Payment
from ..services.payment_service import PaymentService
from message.views import notify_discord

logger = logging.getLogger(__name__)


@csrf_exempt
def create_payment(request):
    """Cria um novo pagamento (suporta plano único ou carrinho com múltiplos itens)"""
    # API: retornar JSON claro quando não autenticado em vez de redirecionar para login
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return JsonResponse({"error": "not_authenticated"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    gateway = data.get("gateway")
    items = data.get("products") or data.get("items")
    
    if not gateway:
        return JsonResponse({"error": "missing_gateway"}, status=400)
    
    # Validar gateway suportado
    if gateway not in PaymentService.GATEWAY_MAP:
        return JsonResponse({
            "error": "unsupported_gateway"
        }, status=400)
    
    try:
        # Se 'items' está presente, usar API de carrinho
        if items is not None:
            if not isinstance(items, list) or len(items) == 0:
                return JsonResponse({"error": "items_must_be_non_empty_list"}, status=400)
            payment = PaymentService.create_payment_with_items(
                user=request.user,
                gateway_name=gateway,
                items=items,
                currency=data.get("currency", "BRL"),
                email=data.get("email")
            )
        else:
            payment = PaymentService.create_payment(
                user=request.user,
                gateway_name=gateway,
                currency=data.get("currency", "BRL")
            )
        
        # Incluir itens na resposta se existirem
        payment_items = []
        if hasattr(payment, 'items'):
            payment_items = [
                {
                    "type": item.item_type,
                    "name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "total_price": str(item.total_price),
                }
                for item in payment.items.all()
            ]

        notify_discord(request.user, "generated_buy", payment.amount, "created")

        # Se o gateway retornou um link de checkout (init_point), redirecionar o usuário
        gateway_response = getattr(payment, 'gateway_response', None) or {}
        # Caso gateway_response seja string, tentar desserializar
        if isinstance(gateway_response, str):
            try:
                gateway_response = json.loads(gateway_response)
            except Exception:
                # mantem como string se não for JSON
                gateway_response = {"raw": gateway_response}

        init_point = None
        if isinstance(gateway_response, dict):
            # Usar sempre o `init_point` quando disponível; se ausente,
            # cair para `sandbox_init_point` como fallback.
            init_point = gateway_response.get('init_point')

        if init_point:

            # Garantir que o objeto gateway_response retornado ao cliente contenha
            # a chave `payment_url` usada pelo frontend existente.
            payment_gateway_response = {}
            if isinstance(gateway_response, dict):
                payment_gateway_response.update(gateway_response)
            else:
                # gateway_response pode ser string ou None; normalizar para dict
                payment_gateway_response["raw"] = gateway_response

            # Inserir payment_url apontando para init_point (compatibilidade frontend)
            payment_gateway_response["payment_url"] = init_point

            # Construir payload incluindo o objeto `payment` esperado pelo frontend
            resp = JsonResponse({
                "status": "success",
                "redirect_url": init_point,
                "payment_gateway_response": payment_gateway_response,
                "payment": {
                    "transaction_id": payment.transaction_id,
                    "gateway": payment.gateway,
                    "plan": payment.plan,
                    "amount": f"{payment.amount:.2f}",
                    "currency": payment.currency,
                    "status": payment.status,
                    "gateway_payment_id": payment.gateway_payment_id,
                    "gateway_response": payment_gateway_response,
                    "items": payment_items,
                    "created_at": payment.created_at.isoformat(),
                }
            }, status=201)

            # Incluir header Location para clientes que checam o header
            resp["Location"] = init_point
            return resp

            # Requisição normal de navegador -> 302
            return HttpResponseRedirect(init_point)

        # Caso não haja init_point, retorna o JSON com os detalhes do pagamento
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
                "items": payment_items,
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
    payments = Payment.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')[:20]
    
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
                "items": [
                    {
                        "type": item.item_type,
                        "name": item.item_name,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                        "total_price": str(item.total_price),
                    }
                    for item in p.items.all()
                ],
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in payments
        ]
    })


# Função utilitária para montar contexto da página de sucesso de pagamento
def get_payment_success_context(request, consulta_gateway_func):
    # Permite múltiplos nomes de parâmetro para compatibilidade
    session_id = (
        request.GET.get('session_id')
        or request.GET.get('checkout_session_id')
        or request.GET.get('session')
        or request.GET.get('id')
        or request.GET.get('transaction_id')
    )
    context = {
        'session_id': session_id,
        'stripe_available': False,
        'payment_status': None,
        'amount': None,
        'currency': None,
        'stripe_error': None,
    }
    if consulta_gateway_func:
        try:
            payment_data = consulta_gateway_func(session_id)
            context.update(payment_data)
        except Exception as e:
            logging.exception(f'Erro ao consultar gateway: %s', e)
            context['stripe_error'] = str(e)
    return context





class SuccessView(TemplateView):
    template_name = "core/success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Detecta gateway dinamicamente
        request = self.request
        # Exibe todos os valores relevantes da request para debug
        session_id = (
            request.GET.get('session_id')
            or request.GET.get('checkout_session_id')
            or request.GET.get('session')
            or request.GET.get('id')
            or request.GET.get('transaction_id')
        )
        # Heurística simples: se id começa com 'abacate', usa abacatepay, senão usa stripe
        if session_id and str(session_id).startswith('abacate'):
            consulta_func = get_abacate_payment_data
        else:
            consulta_func = get_stripe_payment_data
        context.update(get_payment_success_context(request, consulta_func))
        return context


from django.views.generic import TemplateView
class CancelView(TemplateView):
    """Página de cancelamento do checkout."""
    template_name = "core/cancel.html"
