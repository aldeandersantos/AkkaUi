from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from ..models import Favorite
from core.models import SvgFile
import json


@login_required
def favoritos(request):
    """Página de favoritos do usuário"""
    user = request.user
    
    # Obter ou criar o objeto de favoritos do usuário
    favorite_obj, created = Favorite.objects.get_or_create(user=user)
    
    # Obter os SVGs favoritos
    svg_ids = favorite_obj.svg_ids if favorite_obj.svg_ids else []
    favorite_svgs = SvgFile.objects.filter(id__in=svg_ids, is_public=True).order_by('-uploaded_at')
    
    # Adicionar informação de acesso para cada SVG
    for svg in favorite_svgs:
        access_type = svg.user_access_type(user)
        svg.purchased_by_user = access_type == 'owned'
        svg.vip_access = access_type == 'vip'
    
    context = {
        'favorite_svgs': favorite_svgs,
        'total_favorites': len(svg_ids),
    }
    
    return render(request, "usuario/favoritos.html", context)


@login_required
@require_POST
def toggle_favorite(request):
    """API endpoint para adicionar/remover um SVG dos favoritos"""
    try:
        data = json.loads(request.body)
        svg_id = data.get('svg_id')
        
        if not svg_id:
            return JsonResponse({'error': 'svg_id é obrigatório'}, status=400)
        
        # Verificar se o SVG existe
        try:
            svg = SvgFile.objects.get(id=svg_id, is_public=True)
        except SvgFile.DoesNotExist:
            return JsonResponse({'error': 'SVG não encontrado'}, status=404)
        
        # Obter ou criar o objeto de favoritos
        favorite_obj, created = Favorite.objects.get_or_create(user=request.user)
        
        # Garantir que svg_ids é uma lista
        if not isinstance(favorite_obj.svg_ids, list):
            favorite_obj.svg_ids = []
        
        # Toggle: se já está nos favoritos, remove; se não está, adiciona
        if svg_id in favorite_obj.svg_ids:
            favorite_obj.svg_ids.remove(svg_id)
            is_favorited = False
            message = 'SVG removido dos favoritos'
        else:
            favorite_obj.svg_ids.append(svg_id)
            is_favorited = True
            message = 'SVG adicionado aos favoritos'
        
        favorite_obj.save()
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'message': message,
            'total_favorites': len(favorite_obj.svg_ids)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_favorites(request):
    """API endpoint para obter a lista de IDs dos favoritos do usuário"""
    try:
        favorite_obj, created = Favorite.objects.get_or_create(user=request.user)
        svg_ids = favorite_obj.svg_ids if favorite_obj.svg_ids else []
        
        return JsonResponse({
            'success': True,
            'favorite_ids': svg_ids,
            'total_favorites': len(svg_ids)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
