#!/bin/bash
# Script para configurar thumbnails no Linux/Mac
# Execute: bash fix_thumbnails_linux.sh

echo "============================================================"
echo "FIX THUMBNAILS - Linux/Mac"
echo "============================================================"
echo ""

# Verifica se env/.env existe
if [ ! -f "env/.env" ]; then
    echo "Criando arquivo env/.env..."
    mkdir -p env
    touch env/.env
fi

# Adiciona configurações necessárias
echo "Configurando thumbnails para funcionar..."
echo "PROD=True" >> env/.env
echo "USE_NGINX=False" >> env/.env
echo "SECRET_KEY=dev-secret-change-me-in-production" >> env/.env
echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> env/.env

echo ""
echo "✓ Configuração concluída!"
echo ""
echo "Próximos passos:"
echo "1. Execute: python manage.py runserver"
echo "2. Acesse: http://localhost:8000/"
echo "3. Thumbnails devem aparecer!"
echo ""
echo "⚠️  AVISO: Esta configuração é para TESTE."
echo "   Para produção, configure Nginx (ver nginx_protected_media.conf)"
echo ""
echo "============================================================"
