import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import Purchase
from ..serializers import PurchasedSvgSerializer
from core.models import SvgFile


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


@login_required
def purchased_svgs_api(request, user_id):
    """
    API endpoint que retorna os SVGs comprados pelo usuário.
    Apenas o próprio usuário pode acessar suas compras.
    """
    if request.user.id != user_id:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    if request.user.is_vip:
        return JsonResponse({
            'is_vip': True,
            'message': 'Usuário VIP tem acesso a todos os SVGs',
            'purchases': []
        })
    
    purchases = Purchase.objects.filter(user=request.user).select_related('svg').order_by('-purchased_at')
    serializer = PurchasedSvgSerializer(purchases, many=True)
    
    return JsonResponse({
        'is_vip': False,
        'purchases': serializer.data
    })


@csrf_exempt
@login_required
def create_purchase(request):
    """
    Endpoint POST para criar uma nova compra.
    Verifica se o usuário já comprou o SVG antes de criar.
    """
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)
    
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
    price = data.get("price", svg.price)
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
