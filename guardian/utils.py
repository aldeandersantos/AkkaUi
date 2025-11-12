"""
Utilitários para o app guardian
"""
from django.conf import settings
import os


def build_internal_media_url(file_path: str) -> str:
    """
    Constrói a URL interna do Nginx a partir do caminho do arquivo.
    
    Args:
        file_path: Caminho relativo ao MEDIA_ROOT
        
    Returns:
        URL completa para X-Accel-Redirect
    """
    # Obtém o prefixo interno configurado
    internal_url = getattr(settings, 'INTERNAL_MEDIA_URL', '/internal_media/')
    
    # Garante que termina com /
    if not internal_url.endswith('/'):
        internal_url += '/'
    
    # Normaliza o file_path para prevenir directory traversal
    # os.path.normpath já lida com separadores de path multiplataforma
    normalized_path = os.path.normpath(file_path)
    
    # Remove separadores de path iniciais
    normalized_path = normalized_path.lstrip(os.sep)
    
    # Verifica se o caminho normalizado não tenta escapar
    if normalized_path.startswith('..'):
        raise ValueError("Caminho de arquivo inválido: tentativa de directory traversal")

    # Garantir que usamos barras '/' na URL interna (Nginx espera paths estilo URL)
    normalized_path = normalized_path.replace(os.sep, '/')

    return f"{internal_url}{normalized_path}"
