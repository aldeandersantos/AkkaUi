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
- ✅ Regras de acesso baseadas em:
  - SVG público: qualquer um pode ver
  - SVG privado: apenas usuários autenticados
  - SVG pago: apenas donos, compradores ou VIPs

### 3. Guardian URLs (`guardian/urls.py`)
- ✅ Nova rota: `/guardian/thumbnail/<int:svg_id>/`

### 4. Template (`templates/core/partials/item_card.html`)
- ✅ Substituído `{{ item.thumbnail.url }}` por `{{ item.get_thumbnail_url }}`
- ✅ Aplicado em 2 localizações: card preview e modal preview

### 5. Nginx (`nginx_protected_media.conf`)
- ✅ Documentação atualizada sobre bloqueio de `/media/`
- ✅ Instruções claras sobre proteção completa

### 6. Script de Migração (`migrate_thumbnails_to_private.py`)
- ✅ Move thumbnails existentes de `thumbnails/` para `private/thumbnails/`
- ✅ Atualiza banco de dados automaticamente
- ✅ Remove diretório antigo se vazio

### 7. Documentação (`guardian/README.md`)
- ✅ Seção completa sobre proteção de thumbnails
- ✅ Exemplos de uso
- ✅ Regras de acesso documentadas

## Como Funciona Agora

### Upload de Novo SVG
1. Usuário faz upload de SVG com thumbnail
2. Thumbnail é salva automaticamente em `media/private/thumbnails/`
3. Registro no banco aponta para o caminho privado

### Acesso à Thumbnail
1. Template usa `{{ item.get_thumbnail_url }}`
2. Gera URL: `/guardian/thumbnail/<id>/`
3. Guardian valida acesso baseado nas regras do SVG
4. Se autorizado, retorna X-Accel-Redirect
5. Nginx serve o arquivo (usuário nunca vê caminho real)

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

1. **Thumbnails não aparecem:**
   - Verifique se executou o script de migração
   - Confirme que Nginx está configurado corretamente
   - Verifique logs: `tail -f /var/log/nginx/error.log`

2. **403 Forbidden:**
   - Verifique regras de acesso do SVG (is_public, is_paid, etc.)
   - Confirme que usuário tem permissões adequadas

3. **X-Accel-Redirect não funciona:**
   - Confirme que `internal` está presente no location /internal_media/
   - Verifique se o alias aponta para MEDIA_ROOT correto

## Conclusão

Todos os arquivos de mídia (thumbnails e FileAssets) agora estão **completamente protegidos**. O acesso é validado pelo Django antes do Nginx servir os arquivos, garantindo segurança sem sacrificar performance.
