from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404, FileResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
import os

from .models import FileAsset
from .utils import build_internal_media_url


@login_required
def protected_media(request, file_id):
    """
    View que verifica autenticação e retorna o cabeçalho X-Accel-Redirect
    para permitir que o Nginx sirva o arquivo protegido.
    
    O usuário deve estar autenticado e ser o dono do arquivo.
    """
    file_asset = get_object_or_404(FileAsset, id=file_id)
    
    # Verifica se o usuário é o dono do arquivo
    if file_asset.owner != request.user:
        raise PermissionDenied("Você não tem permissão para acessar este arquivo.")
    
    # Em desenvolvimento, serve o arquivo diretamente
    if settings.DEBUG:
        file_path = os.path.join(settings.MEDIA_ROOT, file_asset.file_path)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'))
        raise Http404("Arquivo não encontrado")
    
    # Em produção, usa X-Accel-Redirect para Nginx servir o arquivo
    redirect_path = build_internal_media_url(file_asset.file_path)
    response = HttpResponse()
    response['X-Accel-Redirect'] = redirect_path
    response['Content-Type'] = ''  # Deixa o Nginx determinar o tipo
    
    return response


def protected_thumbnail(request, svg_id):
    """
    View que serve thumbnails de SVGs com controle de acesso.
    
    Permite acesso quando requisitado através de navegadores no site,
    bloqueando acesso direto via ferramentas como curl, wget, Postman.
    
    Verificação de acesso:
    1. Verifica se é requisição de navegador (Accept header)
    2. Valida permissões baseadas no tipo de SVG
    """
    from core.models import SvgFile
    from django.http import FileResponse
    import mimetypes
    
    svg = get_object_or_404(SvgFile, id=svg_id)
    
    # Se não tem thumbnail, retorna 404
    if not svg.thumbnail:
        raise Http404("Thumbnail não encontrada")
    
    # Verifica se a requisição vem de um navegador legítimo
    # Navegadores sempre enviam Accept header com image/* para tags <img>
    accept_header = request.META.get('HTTP_ACCEPT', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referer = request.META.get('HTTP_REFERER', '')
    host = request.get_host()
    
    # Considera "from site" se:
    # 1. Tem referer do próprio site OU
    # 2. É navegador (Accept com image/*) e não é tool de linha de comando
    is_from_site = (referer and (host in referer or f"://{host}" in referer))
    is_browser = 'image/' in accept_header and user_agent and 'Mozilla' in user_agent
    
    # Bloqueia ferramentas de acesso direto (curl, wget, Postman sem referer)
    if not is_from_site and not is_browser:
        # Acesso via ferramenta - verifica se usuário tem permissão especial
        if not request.user.is_authenticated:
            raise PermissionDenied("Acesso direto não permitido. Visualize através do site.")
        
        # Usuário autenticado via ferramenta - permite apenas para donos e VIPs
        if not (request.user == svg.owner or (hasattr(request.user, 'is_vip') and request.user.is_vip)):
            raise PermissionDenied("Acesso direto não permitido. Visualize através do site.")
    
    # Requisição válida - verifica permissões baseadas no SVG
    if not svg.is_public:
        # SVG privado ou pago - exige autenticação para ver no site
        if not request.user.is_authenticated:
            raise PermissionDenied("Autenticação necessária para visualizar esta thumbnail.")
        
        # Verifica se tem acesso específico
        access_type = svg.user_access_type(request.user)
        if access_type == 'locked':
            raise PermissionDenied("Você não tem acesso a esta thumbnail.")
    
    # Em desenvolvimento, serve o arquivo diretamente
    if settings.DEBUG:
        # Usa o caminho do arquivo da thumbnail
        file_path = svg.thumbnail.path
        if os.path.exists(file_path):
            # Detecta o tipo MIME do arquivo
            content_type, _ = mimetypes.guess_type(file_path)
            response = FileResponse(open(file_path, 'rb'))
            if content_type:
                response['Content-Type'] = content_type
            return response
        raise Http404("Thumbnail não encontrada")
    
    # Em produção, usa X-Accel-Redirect para Nginx servir o arquivo
    redirect_path = build_internal_media_url(svg.thumbnail.name)
    response = HttpResponse()
    response['X-Accel-Redirect'] = redirect_path
    response['Content-Type'] = ''  # Deixa o Nginx determinar o tipo
    
    return response
