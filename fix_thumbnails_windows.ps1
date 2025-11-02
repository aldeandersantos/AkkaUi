# Script PowerShell para configurar thumbnails no Windows
# Execute: .\fix_thumbnails_windows.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "FIX THUMBNAILS - Windows" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se env/.env existe
$envPath = "env\.env"
if (-Not (Test-Path $envPath)) {
    Write-Host "Criando arquivo env/.env..." -ForegroundColor Yellow
    New-Item -Path "env" -ItemType Directory -Force | Out-Null
    New-Item -Path $envPath -ItemType File -Force | Out-Null
}

# Adiciona configurações necessárias
Write-Host "Configurando thumbnails para funcionar..." -ForegroundColor Green
Add-Content -Path $envPath -Value "PROD=True"
Add-Content -Path $envPath -Value "USE_NGINX=False"
Add-Content -Path $envPath -Value "SECRET_KEY=dev-secret-change-me-in-production"
Add-Content -Path $envPath -Value "ALLOWED_HOSTS=localhost,127.0.0.1"

Write-Host ""
Write-Host "✓ Configuração concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Execute: python manage.py runserver" -ForegroundColor White
Write-Host "2. Acesse: http://localhost:8000/" -ForegroundColor White
Write-Host "3. Thumbnails devem aparecer!" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  AVISO: Esta configuração é para TESTE." -ForegroundColor Yellow
Write-Host "   Para produção, configure Nginx (ver nginx_protected_media.conf)" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
