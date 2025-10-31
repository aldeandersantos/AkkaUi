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
    
    Regras de acesso:
    - SVGs públicos: qualquer um pode ver a thumbnail
    - SVGs privados: apenas usuários autenticados podem ver
    - SVGs pagos: apenas donos, compradores ou VIPs podem ver
    """
    from core.models import SvgFile
    
    svg = get_object_or_404(SvgFile, id=svg_id)
    
    # Se não tem thumbnail, retorna 404
    if not svg.thumbnail:
        raise Http404("Thumbnail não encontrada")
    
    # Verifica acesso baseado nas regras do SvgFile
    if svg.is_public:
        # SVG público - qualquer um pode ver
        pass
    elif not request.user.is_authenticated:
        # SVG privado e usuário não autenticado
        raise PermissionDenied("Autenticação necessária para visualizar esta thumbnail.")
    else:
        # SVG privado ou pago - verifica se tem acesso
        access_type = svg.user_access_type(request.user)
        if access_type == 'locked':
            raise PermissionDenied("Você não tem acesso a esta thumbnail.")
    
    # Em desenvolvimento, serve o arquivo diretamente
    if settings.DEBUG:
        # Usa o caminho do arquivo da thumbnail
        file_path = svg.thumbnail.path
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'))
        raise Http404("Thumbnail não encontrada")
    
    # Em produção, usa X-Accel-Redirect para Nginx servir o arquivo
    redirect_path = build_internal_media_url(svg.thumbnail.name)
    response = HttpResponse()
    response['X-Accel-Redirect'] = redirect_path
    response['Content-Type'] = ''  # Deixa o Nginx determinar o tipo
    
    return response
