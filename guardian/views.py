from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required

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
        raise Http404("Arquivo não encontrado ou você não tem permissão para acessá-lo.")
    
    # Constrói o caminho interno do Nginx usando o utilitário seguro
    redirect_path = build_internal_media_url(file_asset.file_path)
    
    # Retorna uma resposta vazia com o cabeçalho X-Accel-Redirect
    response = HttpResponse()
    response['X-Accel-Redirect'] = redirect_path
    response['Content-Type'] = ''  # Deixa o Nginx determinar o tipo
    
    return response
