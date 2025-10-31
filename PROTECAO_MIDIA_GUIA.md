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
- ✅ **Suporte a desenvolvimento**: Em DEBUG=True, serve arquivos diretamente via FileResponse
- ✅ **Suporte a produção**: Em DEBUG=False, usa X-Accel-Redirect para Nginx
- ✅ Regras de acesso baseadas em:
  - SVG público: qualquer um pode ver
  - SVG privado: apenas usuários autenticados
  - SVG pago: apenas donos, compradores ou VIPs

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

### Desenvolvimento (DEBUG=True)
1. Views do guardian servem arquivos protegidos diretamente via FileResponse
2. **SEGURANÇA**: Arquivos em `/media/private/` NÃO são acessíveis diretamente - sempre via guardian
3. Arquivos públicos em `/media/` (exceto private/) podem ser acessados normalmente
4. CSS e static files servidos automaticamente pelo Django
5. Thumbnails funcionam imediatamente sem configurar Nginx

### Produção (DEBUG=False)
1. Views do guardian retornam X-Accel-Redirect
2. Nginx intercepta e serve os arquivos protegidos
3. Nginx bloqueia TODO acesso direto a `/media/` (retorna 403)
4. CSS e static files devem ser coletados e servidos pelo Nginx

### Proteção de Arquivos Privados

**Em qualquer modo (desenvolvimento ou produção):**
- ✅ Arquivos em `/media/private/` **nunca** são servidos diretamente
- ✅ Acesso a `/media/private/thumbnails/arquivo.jpg` retorna 404
- ✅ Único acesso: via `/guardian/thumbnail/<id>/` com validação
- ✅ Guardian verifica permissões antes de servir

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

### 1. Aplicar Migrations
```bash
cd /path/to/AkkaUi
python manage.py migrate core
```

### 2. Migrar Thumbnails Existentes
```bash
python migrate_thumbnails_to_private.py
```

**O que esse script faz:**
- Move arquivos físicos de `media/thumbnails/` para `media/private/thumbnails/`
- Atualiza campo `thumbnail` de cada SvgFile no banco
- Remove diretório antigo se estiver vazio
- Mostra relatório detalhado de migração

### 3. Configurar Nginx

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
```

**Atenção:**
- Substitua `/caminho/absoluto/para/media/` pelo caminho real do seu MEDIA_ROOT
- Exemplo: `/home/user/AkkaUi/media/`
- O bloqueio `/media/` é ESSENCIAL para segurança

### 4. Recarregar Nginx
```bash
sudo nginx -t  # Testa configuração
sudo systemctl reload nginx
```

### 5. Testar

#### Teste 1: Upload de Novo SVG
1. Faça login na aplicação
2. Faça upload de um SVG com thumbnail
3. Verifique que a thumbnail aparece corretamente
4. Abra DevTools → Network
5. Confirme que a URL é `/guardian/thumbnail/<id>/`

#### Teste 2: Acesso Direto Bloqueado
1. Tente acessar diretamente: `http://seu-site.com/media/private/thumbnails/arquivo.jpg`
2. Deve receber **403 Forbidden**

#### Teste 3: Regras de Acesso
- **SVG Público**: Thumbnail visível para todos
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

### 1. ✅ IMPLEMENTADO: Bloquear acesso direto mas permitir no site

**Requisito**: Thumbnails visíveis no site, mas URL não acessível diretamente.

**Solução implementada** (Commit atual):
- Verifica **HTTP Referer** - se vem de uma página do site, permite
- Acesso direto (URL no navegador ou Postman sem referer): Bloqueado
- Exceção: Donos do SVG e usuários VIP podem acessar diretamente

**Teste de comportamento:**
```bash
# Acesso direto sem referer: BLOQUEADO (403)
curl -I http://localhost:8000/guardian/thumbnail/22/

# Acesso com referer do site: PERMITIDO (200)
curl -I -H "Referer: http://localhost:8000/pt-br/" http://localhost:8000/guardian/thumbnail/22/

# No navegador: <img src="/guardian/thumbnail/22/"> funciona normalmente
```

**Comportamento:**
- ✅ Usuários veem thumbnails normalmente nas páginas
- ❌ Usuários NÃO podem copiar/colar URL em nova aba
- ✅ Donos e VIPs têm acesso direto especial

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

# Deve exigir login (302 redirect)
curl -I http://localhost:8000/guardian/thumbnail/1/
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

**✅ SOLUÇÃO CORRIGIDA** (Commit atual):

Agora usa `django.contrib.staticfiles.views.serve` que procura arquivos em:
- `STATIC_ROOT` (arquivos coletados via collectstatic)
- `STATICFILES_DIRS` (arquivos do projeto)

**Como usar com DEBUG=False:**

**Passo 1 - Coletar arquivos estáticos:**
```bash
python manage.py collectstatic --noinput
```

**Passo 2 - Habilitar servir via Django:**
```bash
# No terminal (Linux/Mac):
export DEBUG=False
export SERVE_STATIC=true
python manage.py runserver

# No Windows (CMD):
set DEBUG=False
set SERVE_STATIC=true
python manage.py runserver

# No Windows (PowerShell):
$env:DEBUG="False"
$env:SERVE_STATIC="true"
python manage.py runserver
```

**Importante**: Esta solução é para **testes locais**. Em produção real, use Nginx:

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
