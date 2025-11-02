#!/usr/bin/env python3
"""
Script de teste para verificar se thumbnails estão funcionando.
Simula o comportamento do Django com PROD=True e USE_NGINX=False/True.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
os.environ['PROD'] = 'True'

import django
django.setup()

from django.conf import settings
from core.models import SvgFile

def test_thumbnails():
    print("=" * 70)
    print("TESTE DE THUMBNAILS - AkkaUi")
    print("=" * 70)
    print()
    
    # Mostra configuração atual
    print(f"Configuração Atual:")
    print(f"  PROD: {settings.PROD}")
    print(f"  DEBUG: {settings.DEBUG}")
    print(f"  USE_NGINX: {settings.USE_NGINX}")
    print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print()
    
    # Conta SVGs com thumbnails
    svgs_with_thumbnails = SvgFile.objects.exclude(thumbnail='').exclude(thumbnail__isnull=True)
    total_svgs = SvgFile.objects.count()
    
    print(f"SVGs no banco:")
    print(f"  Total: {total_svgs}")
    print(f"  Com thumbnails: {svgs_with_thumbnails.count()}")
    print()
    
    if svgs_with_thumbnails.exists():
        print("Exemplo de SVG com thumbnail:")
        svg = svgs_with_thumbnails.first()
        print(f"  ID: {svg.pk}")
        print(f"  Title: {svg.title_name or 'Sem título'}")
        print(f"  Thumbnail path: {svg.thumbnail.name}")
        print(f"  Thumbnail URL: {svg.get_thumbnail_url()}")
        
        # Verifica se arquivo existe
        thumbnail_full_path = os.path.join(settings.MEDIA_ROOT, svg.thumbnail.name)
        exists = os.path.exists(thumbnail_full_path)
        print(f"  Arquivo existe: {'✓ Sim' if exists else '✗ Não'}")
        
        if exists:
            size = os.path.getsize(thumbnail_full_path)
            print(f"  Tamanho: {size:,} bytes")
    else:
        print("⚠️  Nenhum SVG com thumbnail encontrado no banco.")
        print("   Para testar, adicione SVGs com thumbnails via admin.")
    
    print()
    print("=" * 70)
    print("COMPORTAMENTO ESPERADO:")
    print("=" * 70)
    
    if settings.USE_NGINX:
        print("✓ USE_NGINX=True")
        print("  → Django retorna X-Accel-Redirect")
        print("  → Nginx serve o arquivo (eficiente e seguro)")
        print("  → Se Nginx NÃO estiver configurado, thumbnails NÃO aparecerão")
        print()
        print("  Para testar SEM Nginx, configure:")
        print("  export USE_NGINX=False")
    else:
        print("⚠️  USE_NGINX=False (Modo de teste)")
        print("  → Django serve arquivo diretamente via FileResponse")
        print("  → Funciona mas é menos eficiente")
        print("  → Logs mostram: 'AVISO DE SEGURANÇA'")
        print("  → Configure Nginx para produção final")
    
    print()
    print("Para testar no navegador:")
    print(f"1. python manage.py runserver")
    print(f"2. Acesse: http://localhost:8000/guardian/thumbnail/1/")
    print(f"3. Verifique os logs do servidor")
    print()

if __name__ == '__main__':
    test_thumbnails()
