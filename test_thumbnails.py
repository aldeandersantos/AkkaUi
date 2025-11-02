#!/usr/bin/env python3
"""
Script de teste para verificar se thumbnails estão funcionando.
Detecta problemas comuns e sugere soluções.
"""

import os
import sys
import platform
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
    
    # Detecta sistema operacional
    sistema = platform.system()
    is_windows = sistema == 'Windows'
    
    # Mostra configuração atual
    print(f"Configuração Atual:")
    print(f"  Sistema: {sistema}")
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
        thumbnail_full_path = Path(settings.MEDIA_ROOT) / svg.thumbnail.name
        exists = thumbnail_full_path.exists()
        print(f"  Arquivo existe: {'✓ Sim' if exists else '✗ Não'}")
        
        if exists:
            size = thumbnail_full_path.stat().st_size
            print(f"  Tamanho: {size:,} bytes")
    else:
        print("⚠️  Nenhum SVG com thumbnail encontrado no banco.")
        print("   Para testar, adicione SVGs com thumbnails via admin.")
    
    print()
    print("=" * 70)
    print("DIAGNÓSTICO E SOLUÇÃO:")
    print("=" * 70)
    print()
    
    if settings.USE_NGINX:
        print("❌ PROBLEMA IDENTIFICADO:")
        print("  → USE_NGINX=True mas Nginx provavelmente NÃO está configurado")
        print("  → Thumbnails NÃO aparecerão no frontend")
        print()
        print("✅ SOLUÇÃO RÁPIDA (Teste Imediato):")
        print()
        
        if is_windows:
            print("  No Windows PowerShell, execute:")
            print()
            print("  # 1. Configure USE_NGINX=False no env/.env:")
            print('  Add-Content -Path "env\\.env" -Value "USE_NGINX=False"')
            print()
            print("  # 2. Restart o servidor")
            print("  python manage.py runserver")
        else:
            print("  No terminal Linux/Mac, execute:")
            print()
            print("  # 1. Configure USE_NGINX=False no env/.env:")
            print('  echo "USE_NGINX=False" >> env/.env')
            print()
            print("  # 2. Restart o servidor")
            print("  python manage.py runserver")
        
        print()
        print("  ✓ Thumbnails funcionarão imediatamente!")
        print("  ⚠️  Você verá warnings nos logs (normal para teste)")
        print()
        print("📚 Para configurar Nginx depois (produção final):")
        print("  → Ver: nginx_protected_media.conf")
        print("  → Ver: GUIA_RAPIDO_THUMBNAILS.md")
        
    else:
        print("✓ USE_NGINX=False (Modo de teste)")
        print("  → Django serve arquivo diretamente via FileResponse")
        print("  → Thumbnails DEVEM aparecer no frontend")
        print("  → Logs mostram: 'AVISO DE SEGURANÇA' (normal)")
        print()
        print("Se thumbnails ainda não aparecem:")
        print("  1. Verifique se SVGs têm thumbnails cadastradas")
        print("  2. Verifique permissões do diretório media/")
        print("  3. Restart o servidor: python manage.py runserver")
        print()
        print("Para máxima segurança (depois):")
        print("  → Configure Nginx (ver nginx_protected_media.conf)")
        print("  → Remova USE_NGINX=False do .env")
    
    print()
    print("=" * 70)
    print()

if __name__ == '__main__':
    test_thumbnails()
