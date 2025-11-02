# Guardian - Proteção de Arquivos de Mídia com X-Accel-Redirect

## Visão Geral

O app `guardian` implementa uma solução completa para proteger arquivos de mídia privados usando o método de serviço controlado por aplicação (X-Accel-Redirect) para Nginx.

**ATUALIZAÇÃO**: Agora protege **todos os arquivos de mídia**, incluindo thumbnails de SVGs.

## Funcionalidades

- **Controle de Acesso para FileAsset**: Apenas usuários autenticados e donos podem acessar
- **Controle de Acesso para Thumbnails**: Baseado nas regras do SvgFile (público, privado, pago)
- **X-Accel-Redirect**: Usa o Nginx para servir arquivos de forma eficiente após validação
- **Modelo FileAsset**: Armazena metadados dos arquivos protegidos
- **Views Protegidas**: `protected_media` e `protected_thumbnail`

## Arquitetura

```
Cliente → Django (validação de acesso) → X-Accel-Redirect → Nginx (serve arquivo)
```

### Fluxo para FileAsset:
1. Cliente solicita arquivo via `/guardian/download/<file_id>/`
2. Django valida se usuário está autenticado e é dono do arquivo
3. Django retorna cabeçalho `X-Accel-Redirect` com caminho interno
4. Nginx intercepta e serve o arquivo diretamente do disco

### Fluxo para Thumbnails:
1. Cliente solicita thumbnail via `/guardian/thumbnail/<svg_id>/`
2. Django valida acesso baseado nas regras do SvgFile:
   - SVG público: qualquer um pode ver
   - SVG privado: apenas usuários autenticados
   - SVG pago: apenas donos, compradores ou VIPs
3. Django retorna X-Accel-Redirect
4. Nginx serve a thumbnail

## Configuração

### 1. Settings (server/settings.py)

```python
# App já adicionado ao INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'guardian',
]

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
INTERNAL_MEDIA_URL = '/internal_media/'  # Prefixo interno do Nginx

# USE_NGINX controla se usa X-Accel-Redirect ou serve diretamente
# Em desenvolvimento (PROD=False): USE_NGINX=False (serve diretamente via Django)
# Em produção (PROD=True): USE_NGINX=True (usa X-Accel-Redirect com Nginx)
# 
# IMPORTANTE: Em produção, USE_NGINX é sempre True por segurança.
# Nginx DEVE estar configurado corretamente para thumbnails funcionarem.
if PROD:
    USE_NGINX = True  # Obrigatório em produção por segurança
else:
    USE_NGINX = False  # Desenvolvimento serve diretamente
```

### 2. URLs (server/urls.py)

```python
# URLs já configuradas em urlpatterns
path('guardian/', include('guardian.urls')),
```

### 3. Nginx (nginx_protected_media.conf)

Configure o Nginx para usar a diretiva `internal` e `alias`:

```nginx
location /internal_media/ {
    internal;
    alias /path/to/your/project/media/;
}

# IMPORTANTE: Bloquear acesso direto a todos os arquivos de mídia
location /media/ {
    return 403;
}
```

**IMPORTANTE**: 
- Ajuste o caminho `alias` para corresponder ao seu `MEDIA_ROOT`
- O bloqueio `/media/` garante que todos os arquivos sejam servidos via guardian

### 4. Migração de Thumbnails Existentes

Se você já tem thumbnails antigas na pasta `thumbnails/`, execute o script de migração:

```bash
python migrate_thumbnails_to_private.py
```

Este script:
- Move thumbnails de `media/thumbnails/` para `media/private/thumbnails/`
- Atualiza os registros no banco de dados
- Remove o diretório antigo se estiver vazio

## Uso

### 1. Proteção de FileAsset

```python
from guardian.models import FileAsset
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='exemplo')

file_asset = FileAsset.objects.create(
    name='Documento Privado',
    file_path='private/documento.pdf',  # Relativo ao MEDIA_ROOT
    owner=user
)

# Em um template ou view
url = reverse('guardian:protected_media', args=[file_asset.id])
# URL resultante: /guardian/download/1/
```

**Regras de acesso FileAsset:**
- **Usuário autenticado e dono**: Recebe o arquivo via X-Accel-Redirect
- **Usuário não autenticado**: Redirecionado para login
- **Usuário autenticado mas não dono**: Recebe erro 403 (Forbidden)

### 2. Proteção de Thumbnails

Thumbnails agora são automaticamente protegidas. No template:

```django
{% if item.thumbnail %}
    <img src="{{ item.get_thumbnail_url }}" alt="...">
{% endif %}
```

O método `get_thumbnail_url()` retorna a URL protegida via guardian.

**Regras de acesso Thumbnail:**
- **SVG público (`is_public=True`)**: Qualquer um pode ver a thumbnail
- **SVG privado (`is_public=False`)**: Apenas usuários autenticados
- **SVG pago**: Apenas donos, compradores ou usuários VIP
- **SVG sem acesso**: Retorna 403 (Forbidden)

## Modelo FileAsset

```python
class FileAsset(models.Model):
    name = models.CharField(max_length=255)           # Nome descritivo
    file_path = models.CharField(max_length=500)      # Caminho relativo ao MEDIA_ROOT
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
```

## View protected_media

```python
@login_required
def protected_media(request, file_id):
    """
    Verifica autenticação e propriedade do arquivo.
    Retorna X-Accel-Redirect para o Nginx servir o arquivo.
    """
    file_asset = get_object_or_404(FileAsset, id=file_id)
    
    if file_asset.owner != request.user:
        raise PermissionDenied("Sem permissão")
    
    # Retorna cabeçalho X-Accel-Redirect
    response = HttpResponse()
    response['X-Accel-Redirect'] = build_internal_media_url(file_asset.file_path)
    return response
```

## Administração

O modelo `FileAsset` está registrado no Django Admin:

- Acesse em: `/admin/guardian/fileasset/`
- Lista: nome, caminho, dono, data de upload
- Filtros: data de upload, dono
- Busca: nome, caminho, username do dono

## Segurança

1. **Autenticação obrigatória**: Decorator `@login_required`
2. **Verificação de propriedade**: Apenas o dono pode acessar
3. **Nginx internal**: Bloqueia acesso direto aos arquivos
4. **Sem exposição de caminhos**: Clientes não conhecem estrutura de diretórios

## Exemplo de Integração

```python
# views.py
from django.shortcuts import render, redirect
from guardian.models import FileAsset

def upload_private_file(request):
    if request.method == 'POST':
        file = request.FILES['file']
        # Salvar arquivo no MEDIA_ROOT/private/
        file_path = f'private/{file.name}'
        
        # Criar FileAsset
        FileAsset.objects.create(
            name=file.name,
            file_path=file_path,
            owner=request.user
        )
        return redirect('success')
    
    return render(request, 'upload.html')
```

## Testes

Para testar localmente (sem Nginx):

```bash
# Certifique-se de que PROD=False no ambiente ou .env
# Isso configurará USE_NGINX=False e servirá thumbnails diretamente via Django

# Iniciar servidor Django
python manage.py runserver

# Acessar (estando autenticado)
http://localhost:8000/guardian/download/1/
http://localhost:8000/guardian/thumbnail/1/
```

**Nota**: 
- Com `USE_NGINX=False` (desenvolvimento), os arquivos são servidos diretamente via `FileResponse`
- Com `USE_NGINX=True` (produção), o cabeçalho X-Accel-Redirect é enviado para o Nginx processar
- **Em produção, USE_NGINX é sempre True por segurança - Nginx é obrigatório**

## Produção

### Configuração com Nginx (Obrigatório para Produção)

O Nginx é **obrigatório** em produção por questões de segurança e performance. Siga os passos:

#### 1. Configure o Nginx

Use o arquivo `nginx_protected_media.conf` como base. Este arquivo contém:
- Configuração completa do servidor
- Instruções detalhadas de instalação
- Seção de troubleshooting

**Pontos críticos a ajustar:**

```nginx
# Location interna para X-Accel-Redirect
location /internal_media/ {
    internal;
    alias /home/user/AkkaUi/media/;  # AJUSTE ESTE CAMINHO!
}

# Bloqueio de segurança
location /media/ {
    return 403;  # Garante que apenas Django pode autorizar acesso
}
```

#### 2. Instale a configuração

```bash
# Copie o arquivo para sites-available
sudo cp nginx_protected_media.conf /etc/nginx/sites-available/akkaui

# Ajuste os caminhos no arquivo
sudo nano /etc/nginx/sites-available/akkaui

# Crie link simbólico
sudo ln -s /etc/nginx/sites-available/akkaui /etc/nginx/sites-enabled/

# Teste a configuração
sudo nginx -t

# Recarregue o Nginx
sudo systemctl reload nginx
```

#### 3. Configure Django

```bash
# No arquivo .env ou variáveis de ambiente
PROD=True
# USE_NGINX é automaticamente True quando PROD=True (não precisa definir)
```

#### 4. Verifique o funcionamento

O arquivo `nginx_protected_media.conf` contém uma seção completa "VERIFICAÇÃO DE FUNCIONAMENTO" com:
- Como verificar logs do Django
- Como verificar headers da resposta
- Troubleshooting de erros 404/403
- Verificação de permissões

#### 5. Troubleshooting

**Thumbnails não aparecem:**
1. Verifique logs do Django - deve aparecer: `X-Accel-Redirect enviado: /internal_media/...`
2. Verifique se o caminho `alias` no Nginx aponta para o MEDIA_ROOT correto
3. Verifique permissões do diretório `media/` (Nginx precisa ler)
4. Verifique logs do Nginx: `tail -f /var/log/nginx/error.log`

**Erro 404:**
- Caminho `alias` incorreto no Nginx
- Arquivo não existe em MEDIA_ROOT

**Erro 403:**
- Permissões do diretório incorretas
- Nginx não consegue ler os arquivos

## Referências

- [Nginx X-Accel Documentation](https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/)
- [Django File Uploads](https://docs.djangoproject.com/en/stable/topics/http/file-uploads/)
