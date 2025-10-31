# Guardian - Proteção de Arquivos de Mídia com X-Accel-Redirect

## Visão Geral

O app `guardian` implementa uma solução completa para proteger arquivos de mídia privados usando o método de serviço controlado por aplicação (X-Accel-Redirect) para Nginx.

## Funcionalidades

- **Controle de Acesso**: Apenas usuários autenticados e donos do arquivo podem acessá-lo
- **X-Accel-Redirect**: Usa o Nginx para servir arquivos de forma eficiente após validação
- **Modelo FileAsset**: Armazena metadados dos arquivos protegidos
- **View Protegida**: View `protected_media` com `@login_required`

## Arquitetura

```
Cliente → Django (autenticação) → X-Accel-Redirect → Nginx (serve arquivo)
```

1. Cliente solicita arquivo via `/guardian/download/<file_id>/`
2. Django valida se usuário está autenticado e é dono do arquivo
3. Django retorna cabeçalho `X-Accel-Redirect` com caminho interno
4. Nginx intercepta e serve o arquivo diretamente do disco

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

# Opcional: Bloquear acesso direto a /media/
location /media/ {
    return 403;
}
```

**IMPORTANTE**: Ajuste o caminho `alias` para corresponder ao seu `MEDIA_ROOT`.

## Uso

### 1. Criar um FileAsset

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
```

### 2. Acessar o arquivo protegido

```python
# Em um template ou view
url = reverse('guardian:protected_media', args=[file_asset.id])
# URL resultante: /guardian/download/1/
```

### 3. Como funciona

- **Usuário autenticado e dono**: Recebe o arquivo via X-Accel-Redirect
- **Usuário não autenticado**: Redirecionado para login
- **Usuário autenticado mas não dono**: Recebe erro 403 (Forbidden)

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
# Iniciar servidor Django
python manage.py runserver

# Acessar (estando autenticado)
http://localhost:8000/guardian/download/1/
```

**Nota**: Sem Nginx, o cabeçalho X-Accel-Redirect será enviado mas não processado. Para teste completo, configure o Nginx conforme documentado.

## Produção

Em produção:

1. Configure o Nginx com o arquivo `nginx_protected_media.conf`
2. Ajuste o caminho `alias` no Nginx para seu `MEDIA_ROOT`
3. Garanta que o Django não sirva arquivos estáticos/media diretamente
4. Use `collectstatic` para arquivos estáticos
5. Configure permissões adequadas para o diretório `media/`

## Referências

- [Nginx X-Accel Documentation](https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/)
- [Django File Uploads](https://docs.djangoproject.com/en/stable/topics/http/file-uploads/)
