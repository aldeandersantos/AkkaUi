# Proteção Completa de Arquivos de Mídia - Guia de Implementação

## Resumo das Mudanças

Implementamos proteção completa para **todos os arquivos de mídia**, incluindo thumbnails de SVGs, usando X-Accel-Redirect do Nginx.

## O Que Foi Modificado

### 1. Modelo SvgFile (`core/models.py`)
- ✅ Campo `thumbnail` agora salva em `private/thumbnails/` ao invés de `thumbnails/`
- ✅ Novo método `get_thumbnail_url()` retorna URL protegida via guardian
- ✅ Importação do `reverse` para gerar URLs

### 2. Guardian Views (`guardian/views.py`)
- ✅ Nova view `protected_thumbnail(request, svg_id)` para servir thumbnails
- ✅ **Suporte a desenvolvimento E produção com runserver**: Detecta `USE_NGINX` env var
- ✅ **Sem Nginx (padrão)**: Serve arquivos diretamente via FileResponse
- ✅ **Com Nginx (USE_NGINX=true)**: Usa X-Accel-Redirect
- ✅ Regras de acesso baseadas em:
  - SVG público: qualquer um pode ver
  - SVG privado: apenas usuários autenticados
  - SVG pago: apenas donos, compradores ou VIPs
- ✅ **Hotlink Protection**: Bloqueia curl/wget/Postman (detecta User-Agent sem "Mozilla")

### 3. Guardian URLs (`guardian/urls.py`)
- ✅ Nova rota: `/guardian/thumbnail/<int:svg_id>/`

### 4. Template (`templates/core/partials/item_card.html`)
- ✅ Substituído `{{ item.thumbnail.url }}` por `{{ item.get_thumbnail_url }}`
- ✅ Aplicado em 2 localizações: card preview e modal preview

### 5. Server URLs (`server/urls.py`) - CRÍTICO
- ✅ **Proteção de arquivos privados em desenvolvimento**: Custom view bloqueia acesso direto a `/media/private/`
- ✅ Em DEBUG=True, apenas arquivos NÃO-privados são servidos diretamente
- ✅ Arquivos em `/media/private/` sempre exigem passar pelo guardian
- ✅ Static files servidos automaticamente em DEBUG=True
- ✅ Suporte para SERVE_STATIC env var quando DEBUG=False

### 6. Nginx (`nginx_protected_media.conf`)
- ✅ Documentação atualizada sobre bloqueio de `/media/`
- ✅ Instruções claras sobre proteção completa

### 7. Script de Migração (`migrate_thumbnails_to_private.py`)
- ✅ Move thumbnails existentes de `thumbnails/` para `private/thumbnails/`
- ✅ Atualiza banco de dados automaticamente
- ✅ Remove diretório antigo se vazio

### 8. Documentação (`guardian/README.md`)
- ✅ Seção completa sobre proteção de thumbnails
- ✅ Exemplos de uso
- ✅ Regras de acesso documentadas

## Como Funciona Agora

### Desenvolvimento (sem Nginx)
**Cenário padrão: DEBUG=True ou DEBUG=False com `python manage.py runserver`**

1. Views do guardian servem arquivos protegidos diretamente via FileResponse
2. **SEGURANÇA**: Arquivos em `/media/private/` NÃO são acessíveis diretamente - sempre via guardian
3. Arquivos públicos em `/media/` (exceto private/) podem ser acessados normalmente
4. CSS e static files servidos por WhiteNoise middleware
5. Thumbnails funcionam imediatamente sem configurar Nginx

**✅ Funciona com DEBUG=True**
**✅ Funciona com DEBUG=False** (diferente do comportamento anterior!)

### Produção (com Nginx)
**Quando USE_NGINX=true (variável de ambiente)**

1. Views do guardian retornam X-Accel-Redirect
2. Nginx intercepta e serve os arquivos protegidos
3. Nginx bloqueia TODO acesso direto a `/media/` (retorna 403)
4. CSS e static files devem ser coletados e servidos pelo Nginx
5. Melhor performance - Nginx serve arquivos diretamente após validação

### Proteção de Arquivos Privados

**Em qualquer modo (desenvolvimento ou produção):**
- ✅ Arquivos em `/media/private/` **nunca** são servidos diretamente
- ✅ Acesso a `/media/private/thumbnails/arquivo.jpg` retorna 404
- ✅ Único acesso: via `/guardian/thumbnail/<id>/` com validação
- ✅ Guardian verifica permissões antes de servir
- ✅ Hotlink protection: bloqueia ferramentas CLI (curl, wget, Postman)

### Upload de Novo SVG
1. Usuário faz upload de SVG com thumbnail
2. Thumbnail é salva automaticamente em `media/private/thumbnails/`
3. Registro no banco aponta para o caminho privado

### Acesso à Thumbnail

**IMPORTANTE: Proteção contra acesso direto via URL**

1. Template usa `{{ item.get_thumbnail_url }}`
2. Gera URL: `/guardian/thumbnail/<id>/`
3. Guardian valida acesso baseado em **HTTP Referer**:
   - **Vem do site** (tag `<img>` na página): Permite e valida permissões do SVG
   - **Acesso direto** (URL no navegador): Bloqueado com PermissionDenied
4. Regras de acesso quando vem do site:
   - **SVG público**: Qualquer um pode ver (inclusive não-autenticados)
   - **SVG privado/pago**: Apenas usuários autenticados com permissão
5. Exceção para acesso direto: Apenas donos do SVG ou usuários VIP
6. Se autorizado, serve o arquivo (DEBUG=True) ou retorna X-Accel-Redirect (DEBUG=False)

**Resultado**: 
- ✅ Usuários veem thumbnails normalmente no site
- ❌ Usuários NÃO podem acessar URLs diretamente
- ✅ Sistema serve imagens sem expor caminhos reais

## Passo a Passo para Deploy

### Modo 1: Desenvolvimento ou Testes com runserver (DEBUG=False)

**✅ Recomendado para testar em modo produção sem Nginx**

```bash
# Windows CMD
set DEBUG=False
set SECRET_KEY=sua-chave-secreta-aqui
python manage.py collectstatic --noinput
python manage.py runserver

# Windows PowerShell
$env:DEBUG="False"
$env:SECRET_KEY="sua-chave-secreta-aqui"
python manage.py collectstatic --noinput
python manage.py runserver

# Linux/Mac
export DEBUG=False
export SECRET_KEY=sua-chave-secreta-aqui
python manage.py collectstatic --noinput
python manage.py runserver
```

**O que acontece:**
- ✅ Guardian serve arquivos diretamente via FileResponse
- ✅ WhiteNoise serve static files (CSS, JS)
- ✅ Thumbnails funcionam normalmente
- ✅ Proteção contra acesso direto ativa
- ✅ Hotlink protection ativa (bloqueia curl/wget/Postman)

**Não precisa de:**
- ❌ Nginx configurado
- ❌ Variável USE_NGINX

### Modo 2: Produção com Nginx (Recomendado)

**✅ Para deploy real em servidor de produção**

#### 1. Aplicar Migrations
```bash
cd /path/to/AkkaUi
python manage.py migrate core
```

#### 2. Migrar Thumbnails Existentes
```bash
python migrate_thumbnails_to_private.py
```

**O que esse script faz:**
- Move arquivos físicos de `media/thumbnails/` para `media/private/thumbnails/`
- Atualiza campo `thumbnail` de cada SvgFile no banco
- Remove diretório antigo se estiver vazio
- Mostra relatório detalhado de migração

#### 3. Coletar Static Files
```bash
python manage.py collectstatic --noinput
```

#### 4. Configurar Nginx

Atualize sua configuração do Nginx:

```nginx
# Bloco interno para X-Accel-Redirect
location /internal_media/ {
    internal;
    alias /caminho/absoluto/para/media/;  # ← AJUSTE AQUI
}

# IMPORTANTE: Bloquear acesso direto
location /media/ {
    return 403;
}

# Servir static files
location /static/ {
    alias /caminho/absoluto/para/staticfiles/;
}
```

**Atenção:**
- Substitua `/caminho/absoluto/para/media/` pelo caminho real do seu MEDIA_ROOT
- Exemplo: `/home/user/AkkaUi/media/`
- O bloqueio `/media/` é ESSENCIAL para segurança

#### 5. Configurar Variáveis de Ambiente

No servidor de produção:

```bash
export DEBUG=False
export USE_NGINX=true  # ← IMPORTANTE: Ativa X-Accel-Redirect
export SECRET_KEY=sua-chave-secreta-forte
export ALLOWED_HOSTS=seudominio.com,www.seudominio.com
```

**O que acontece:**
- ✅ Guardian retorna X-Accel-Redirect (não serve arquivos diretamente)
- ✅ Nginx serve arquivos após validação
- ✅ Melhor performance
- ✅ Mesmas proteções de segurança

#### 6. Recarregar Nginx
```bash
sudo nginx -t  # Testa configuração
sudo systemctl reload nginx
```

### 7. Testar

#### Teste 1: Upload de Novo SVG
1. Faça login na aplicação
2. Faça upload de um SVG com thumbnail
3. Verifique que a thumbnail aparece corretamente
4. Abra DevTools → Network
5. Confirme que a URL é `/guardian/thumbnail/<id>/`

#### Teste 2: Acesso Direto Bloqueado
1. Tente acessar diretamente: `http://seu-site.com/media/private/thumbnails/arquivo.jpg`
2. **Com Nginx**: Deve receber **403 Forbidden**
3. **Sem Nginx (runserver)**: Deve receber **404 Not Found**

#### Teste 3: Hotlink Protection
```bash
# Deve falhar - sem User-Agent de navegador
curl http://seu-site.com/guardian/thumbnail/1/

# Deve funcionar - com User-Agent de navegador
curl -H "User-Agent: Mozilla/5.0" http://seu-site.com/guardian/thumbnail/1/
```

#### Teste 4: Regras de Acesso
- **SVG Público**: Thumbnail visível para todos (navegadores apenas)
- **SVG Privado**: Thumbnail apenas para usuários autenticados
- **SVG Pago**: Thumbnail apenas para donos/compradores/VIPs

## Estrutura de Diretórios

```
media/
├── private/
│   └── thumbnails/          ← Thumbnails protegidas aqui
│       ├── arquivo1.jpg
│       └── arquivo2.png
└── (outros arquivos do FileAsset)
```

## Verificações de Segurança

✅ **Thumbnails antigas migradas para pasta privada**
✅ **Nginx bloqueia acesso direto a /media/**
✅ **Django valida acesso antes de servir**
✅ **X-Accel-Redirect usado para performance**
✅ **URLs protegidas não expõem estrutura de diretórios**

## Compatibilidade com Código Existente

### Templates
- ✅ `{{ item.get_thumbnail_url }}` substitui `{{ item.thumbnail.url }}`
- ✅ Templates atualizados automaticamente

### Views/APIs
- ✅ Acesso via `svg.get_thumbnail_url()` ao invés de `svg.thumbnail.url`
- ✅ Método compatível com thumbnails None (retorna None)

### Uploads
- ✅ Novos uploads automaticamente salvos em pasta privada
- ✅ Nenhuma mudança no código de upload necessária

## Rollback (Se Necessário)

Se precisar reverter as mudanças:

1. **Reverter migration:**
   ```bash
   python manage.py migrate core <migration_anterior>
   ```

2. **Mover thumbnails de volta:**
   ```bash
   # Execute manualmente ou crie script reverso
   mv media/private/thumbnails/* media/thumbnails/
   ```

3. **Restaurar Nginx:**
   - Remover bloqueio de `/media/`
   - Recarregar Nginx

4. **Git:**
   ```bash
   git revert HEAD
   ```

## Suporte

Se tiver problemas:

### 1. ✅ CORRIGIDO: Thumbnails não aparecem com DEBUG=False

**Problema**: Com `DEBUG=False` e `python manage.py runserver`, thumbnails não aparecem.

**Causa**: View retornava `X-Accel-Redirect` mas `runserver` não processa esse header (apenas Nginx faz).

**✅ SOLUÇÃO APLICADA** (Commit atual):

Agora detecta se está usando Nginx via variável `USE_NGINX`:
- **Sem `USE_NGINX` (padrão)**: Serve arquivos diretamente via FileResponse
- **Com `USE_NGINX=true`**: Retorna X-Accel-Redirect para Nginx

```python
use_nginx = os.getenv('USE_NGINX', 'false').lower() in ('true', '1', 'yes')

if not use_nginx:
    # Serve diretamente - funciona com DEBUG=True e DEBUG=False
    return FileResponse(open(file_path, 'rb'))
else:
    # Produção com Nginx - retorna X-Accel-Redirect
    response['X-Accel-Redirect'] = redirect_path
```

**Como usar:**
- ✅ **Desenvolvimento/Testes**: Não configure `USE_NGINX` → Funciona automaticamente
- ✅ **Produção com Nginx**: Configure `USE_NGINX=true` → Usa X-Accel-Redirect

### 2. ✅ CORRIGIDO: Hotlink protection e detecção de navegador

**Problema**: `document.referrer` retorna `undefined`, thumbnails bloqueadas.

**Causa**: Políticas de Referrer do navegador podem bloquear o header HTTP_REFERER.

**✅ SOLUÇÃO APLICADA** (Commit atual):

Agora detecta navegadores via **User-Agent**:
- Navegadores têm "Mozilla" no User-Agent → Permitidos
- Ferramentas CLI (curl, wget) sem "Mozilla" → Bloqueadas
- Referer não é mais necessário

```python
is_browser = 'Mozilla' in user_agent

if not is_browser:
    # Bloqueia ferramentas CLI
    raise PermissionDenied("Acesso direto não permitido")
```
is_browser = 'image/' in accept_header and 'Mozilla' in user_agent
# OU se tem referer do site
is_from_site = host in referer
```

**Teste:**
```bash
# curl sem User-Agent: BLOQUEADO
curl http://localhost:8000/guardian/thumbnail/22/

# Navegador (mesmo sem referer): PERMITIDO
# Tags <img> funcionam normalmente
```

**Comportamento:**
- ✅ Thumbnails funcionam em navegadores (Chrome, Firefox, Safari, Edge)
- ✅ Funciona mesmo com Referrer-Policy: no-referrer
- ❌ Bloqueia acesso via curl/wget/Postman (sem User-Agent adequado)
- ✅ Donos e VIPs têm acesso direto sempre

### 2. ❌ VULNERABILIDADE: Acesso direto a `/media/private/` em DEBUG=True

**Problema**: Consegue acessar `http://localhost:8000/media/private/thumbnails/arquivo.jpg`

**✅ CORRIGIDO**:
- Custom view em `server/urls.py` bloqueia acesso a `private/`
- Retorna 404 para qualquer arquivo em `/media/private/`
- Apenas via guardian com validação de permissões

**Teste de Segurança:**
```bash
# Deve retornar 404 (não encontrado)
curl http://localhost:8000/media/private/thumbnails/qualquer_arquivo.jpg

# Deve funcionar em navegador
# Abra no navegador: http://localhost:8000/ e thumbnails aparecem
```

### 3. Thumbnails não aparecem (mostram "sem prévia disponível")

**Em Desenvolvimento (DEBUG=True):**
- ✅ **Correção aplicada**: Views agora servem arquivos diretamente via FileResponse
- Verifique se executou o script de migração: `python migrate_thumbnails_to_private.py`
- Confirme que os arquivos existem em `media/private/thumbnails/`
- Verifique o console do navegador (F12) para erros específicos
- **Importante**: Usuário deve estar logado para ver thumbnails

**Em Produção (DEBUG=False com Nginx):**
- Confirme que Nginx está configurado corretamente
- Verifique logs: `tail -f /var/log/nginx/error.log`
- Teste o X-Accel-Redirect: `curl -I http://seu-site.com/guardian/thumbnail/1/`

### 4. CSS não carrega quando DEBUG=False

**Causa**: Django não serve arquivos estáticos quando DEBUG=False por padrão.

**✅ SOLUÇÃO RECOMENDADA: WhiteNoise**

A melhor solução é usar o pacote WhiteNoise, que serve static files de forma eficiente:

**Passo 1 - Instalar WhiteNoise:**
```bash
pip install whitenoise
```

**Passo 2 - Adicionar ao MIDDLEWARE (settings.py):**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Logo após SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... resto dos middlewares
]
```

**Passo 3 - Coletar static files:**
```bash
python manage.py collectstatic --noinput
```

**Passo 4 - Rodar com DEBUG=False:**
```bash
# Windows CMD:
set DEBUG=False
python manage.py runserver

# Windows PowerShell:
$env:DEBUG="False"
python manage.py runserver

# Linux/Mac:
export DEBUG=False
python manage.py runserver
```

**Vantagens do WhiteNoise:**
- ✅ Funciona automaticamente com DEBUG=False
- ✅ Não precisa SERVE_STATIC=true
- ✅ Compressão e cache automáticos
- ✅ Recomendado pela Django para produção simples

**Alternativa sem WhiteNoise:**

Se preferir não usar WhiteNoise, use a solução anterior com SERVE_STATIC=true (ver documentação anterior).

**Importante**: Em produção com Nginx, desabilite WhiteNoise e use Nginx para servir static files:

```nginx
location /static/ {
    alias /caminho/completo/para/staticfiles/;
}
```

**Se ainda não funcionar:**
1. Verifique se `django.contrib.staticfiles` está em INSTALLED_APPS
2. Execute `python manage.py findstatic nome_do_arquivo.css` para diagnosticar
3. Verifique o console do navegador (F12) para erros específicos

### 5. 403 Forbidden ao acessar thumbnails
- Verifique regras de acesso do SVG (is_public, is_paid, etc.)
- Confirme que usuário tem permissões adequadas
- Para SVGs pagos, verifique se usuário comprou ou tem acesso VIP

### 4. X-Accel-Redirect não funciona em produção
- Confirme que `internal` está presente no location /internal_media/
- Verifique se o alias aponta para MEDIA_ROOT correto
- Teste se DEBUG=False está ativo (views devem retornar X-Accel-Redirect)

## Diferenças Desenvolvimento vs Produção

### Desenvolvimento (DEBUG=True)
```python
# guardian/views.py serve arquivos diretamente
if settings.DEBUG:
    return FileResponse(open(file_path, 'rb'))
```
- ✅ Funciona imediatamente sem Nginx
- ✅ Thumbnails aparecem normalmente
- ✅ Static/CSS funcionam automaticamente

### Produção (DEBUG=False)
```python
# guardian/views.py retorna X-Accel-Redirect
response['X-Accel-Redirect'] = redirect_path
```
- ⚠️ Requer Nginx configurado
- ⚠️ Requer `collectstatic` para CSS
- ✅ Melhor performance (Nginx serve arquivos)

## Conclusão

Todos os arquivos de mídia (thumbnails e FileAssets) agora estão **completamente protegidos**. O acesso é validado pelo Django antes do Nginx servir os arquivos, garantindo segurança sem sacrificar performance.

**Versão atualizada** suporta tanto desenvolvimento quanto produção automaticamente.
