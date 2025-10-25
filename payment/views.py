import json
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from abacatepay import AbacatePay
from .services.services_abacate import *
from .models import Purchase
from .serializers import PurchasedSvgSerializer
from core.models import SvgFile


ABACATE_API_TEST_KEY: str = getattr(settings, "ABACATE_API_TEST_KEY", "")


client = AbacatePay(api_key=ABACATE_API_TEST_KEY) if AbacatePay is not None else None


def abacate_status(request):
	"""View simples para verificar se o client do gateway foi configurado.

	Retorna JSON com flag `client_configured` dependendo da presença da chave.
	"""
	return JsonResponse({"client_configured": bool(ABACATE_API_TEST_KEY)})


@csrf_exempt
def simulate_sale(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)


    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    amount = data.get("amount")
    currency = data.get("currency", "BRL")

    if not amount:
        return JsonResponse({"error": "missing_amount"}, status=400)

    if client is not None:
        try:
            payload = {
                "amount": amount,
                "currency": currency,
            }
            result = client.pixQrCode.create(payload)
            gateway_response = norm_response(result)
            return JsonResponse({"status": "created", "gateway_response": gateway_response})
        except Exception as exc:
            return JsonResponse({"status": "error", "detail": str(exc)}, status=502)

    simulated = {"id": "sim_tx_123", "amount": amount, "currency": currency, "status": "created"}
    return JsonResponse({"status": "created", "gateway_response": simulated})


@csrf_exempt
def simulate_confirmation(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    payment_id = data.get("id")
    if not payment_id:
        return JsonResponse({"error": "missing_payment_id"}, status=400)

    status = str(data.get("status"))
    if status != "confirmed":
        return JsonResponse({"error": "invalid_status"}, status=400)

    if client is not None:
        try:
            result = client.pixQrCode.simulate(id=payment_id)
            gateway_response = norm_response(result)
            return JsonResponse({"status": status, "gateway_response": gateway_response})
        except Exception as exc:
            msg = str(exc)
            if "not found" in msg.lower() or "not_found" in msg.lower():
                return JsonResponse({"error": "payment_not_found", "detail": msg}, status=404)
            return JsonResponse({"status": "error", "detail": msg}, status=502)

    simulated_confirmation = {"id": payment_id, "status": status}
    return JsonResponse({"status": status, "gateway_response": simulated_confirmation})


@login_required
def purchased_svgs_api(request, user_id):
    """
    Endpoint GET /api/users/<id>/purchased-svgs
    Retorna lista de SVGs comprados pelo usuário ou todos os SVGs se for VIP.
    Apenas o próprio usuário ou admin pode acessar.
    """
    # Verifica se o usuário pode acessar esses dados
    if request.user.id != user_id and not request.user.is_staff:
        return HttpResponseForbidden(
            json.dumps({"error": "Você não tem permissão para acessar esses dados"}),
            content_type="application/json"
        )
    
    # Se o usuário for VIP, retorna todos os SVGs do catálogo
    if request.user.is_vip:
        all_svgs = SvgFile.objects.filter(is_public=True).order_by('-uploaded_at')
        # Cria uma estrutura similar ao Purchase mas para todos os SVGs
        data = []
        for svg in all_svgs:
            data.append({
                'svg_id': svg.id,
                'title_name': svg.title_name,
                'description': svg.description,
                'thumbnail': svg.thumbnail.url if svg.thumbnail else None,
                'svg_content': svg.get_sanitized_content(),
                'purchased_at': None,  # VIP não tem data de compra
                'price': 0.0,
                'payment_method': 'VIP',
                'is_vip_access': True
            })
        return JsonResponse({
            'is_vip': True,
            'count': len(data),
            'results': data
        })
    
    # Usuário não-VIP: retorna apenas SVGs comprados
    purchases = Purchase.objects.filter(user=request.user).select_related('svg')
    serializer = PurchasedSvgSerializer(purchases, many=True)
    
    return JsonResponse({
        'is_vip': False,
        'count': purchases.count(),
        'results': serializer.data
    })


@login_required
def purchased_svgs_page(request):
    """
    Página HTML que exibe os SVGs comprados pelo usuário.
    Se o usuário for VIP, mostra todos os SVGs do catálogo.
    """
    if request.user.is_vip:
        svgs = SvgFile.objects.filter(is_public=True).order_by('-uploaded_at')
        context = {
            'is_vip': True,
            'svgfiles': svgs,
            'vip_message': 'Você é VIP — tem acesso a todos os SVGs do site'
        }
    else:
        purchases = Purchase.objects.filter(user=request.user).select_related('svg').order_by('-purchased_at')
        svgs = [purchase.svg for purchase in purchases]
        context = {
            'is_vip': False,
            'svgfiles': svgs,
            'purchases': purchases
        }
    
    return render(request, 'payment/purchased_svgs.html', context)


@csrf_exempt
def create_purchase(request):
    """
    Endpoint POST para criar uma nova compra.
    Verifica se o usuário já comprou o SVG antes de criar.
    """
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    svg_id = data.get("svg_id")
    if not svg_id:
        return JsonResponse({"error": "svg_id_required"}, status=400)
    
    # Verifica se o SVG existe
    try:
        svg = SvgFile.objects.get(id=svg_id)
    except SvgFile.DoesNotExist:
        return JsonResponse({"error": "svg_not_found"}, status=404)
    
    # Verifica se o usuário já comprou este SVG
    existing_purchase = Purchase.objects.filter(user=request.user, svg=svg).first()
    if existing_purchase:
        return JsonResponse({
            "error": "duplicate_purchase",
            "message": "Você já comprou este SVG. Use o botão Copiar para acessá-lo."
        }, status=409)
    
    # Cria a compra
    price = data.get("price", 0.0)
    payment_method = data.get("payment_method", "")
    
    purchase = Purchase.objects.create(
        user=request.user,
        svg=svg,
        price=price,
        payment_method=payment_method
    )
    
    serializer = PurchasedSvgSerializer(purchase)
    return JsonResponse({
        "success": True,
        "purchase": serializer.data
    }, status=201)


