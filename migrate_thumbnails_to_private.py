"""
Script de migração para mover thumbnails existentes para pasta privada.

Este script deve ser executado após aplicar as migrations do Django.
Ele move os arquivos físicos de thumbnails/ para private/thumbnails/
e atualiza os registros no banco de dados.

Uso:
    python manage.py shell < migrate_thumbnails_to_private.py

Ou execute diretamente:
    python migrate_thumbnails_to_private.py
"""

import os
import shutil
from pathlib import Path


def migrate_thumbnails():
    """Move thumbnails existentes para pasta privada"""
    
    # Importa os modelos necessários
    import django
    django.setup()
    
    from django.conf import settings
    from core.models import SvgFile
    
    media_root = Path(settings.MEDIA_ROOT)
    old_thumbs_dir = media_root / 'thumbnails'
    new_thumbs_dir = media_root / 'private' / 'thumbnails'
    
    # Cria o diretório de destino se não existir
    new_thumbs_dir.mkdir(parents=True, exist_ok=True)
    
    # Verifica se há thumbnails antigas para migrar
    if not old_thumbs_dir.exists():
        print("✓ Não há pasta thumbnails/ antiga. Nenhuma migração necessária.")
        return
    
    # Lista todos os SVGs com thumbnails
    svgs_with_thumbs = SvgFile.objects.exclude(thumbnail='').exclude(thumbnail__isnull=True)
    migrated_count = 0
    error_count = 0
    
    print(f"Encontrados {svgs_with_thumbs.count()} SVGs com thumbnails para migrar...")
    
    for svg in svgs_with_thumbs:
        old_path = media_root / svg.thumbnail.name
        
        # Verifica se o arquivo ainda está no caminho antigo
        if not old_path.exists():
            print(f"  ⚠ Arquivo não encontrado: {old_path}")
            continue
        
        # Se já está no caminho novo, pula
        if svg.thumbnail.name.startswith('private/thumbnails/'):
            print(f"  ✓ Já migrado: {svg.thumbnail.name}")
            continue
        
        try:
            # Define o novo caminho
            filename = old_path.name
            new_relative_path = f'private/thumbnails/{filename}'
            new_path = media_root / new_relative_path
            
            # Move o arquivo
            shutil.move(str(old_path), str(new_path))
            
            # Atualiza o banco de dados
            svg.thumbnail.name = new_relative_path
            svg.save(update_fields=['thumbnail'])
            
            migrated_count += 1
            print(f"  ✓ Migrado: {filename}")
            
        except Exception as e:
            error_count += 1
            print(f"  ✗ Erro ao migrar {svg.thumbnail.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Migração concluída!")
    print(f"  • Migrados com sucesso: {migrated_count}")
    print(f"  • Erros: {error_count}")
    print(f"{'='*60}")
    
    # Remove o diretório antigo se estiver vazio
    if old_thumbs_dir.exists():
        try:
            old_thumbs_dir.rmdir()
            print("✓ Diretório antigo thumbnails/ removido (estava vazio)")
        except OSError:
            print("⚠ Diretório antigo thumbnails/ não está vazio. Revise manualmente.")


if __name__ == '__main__':
    # Configura o Django se executado diretamente
    import sys
    import os
    
    # Adiciona o diretório do projeto ao path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Configura o settings do Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    
    migrate_thumbnails()
