# Templates Partials

Este diretório contém templates reutilizáveis (partials) usados em várias páginas do AkkaUi.

## item_card.html

Card reutilizável para exibir SvgFile com preview, modal e ações.

### Uso

```django
{% for item in svgfiles %}
  {% include 'core/partials/item_card.html' %}
{% endfor %}
```

### Variável Requerida

- `item` (SvgFile): Objeto do modelo com os campos:
  - `pk` - ID do SVG
  - `title_name` - Nome/título
  - `filename` - Nome do arquivo (fallback)
  - `description` - Descrição (opcional)
  - `thumbnail` - ImageField (opcional)
  - `content` - Conteúdo SVG
  - `get_sanitized_content()` - Método que retorna SVG sanitizado

### Funcionalidades

#### Preview de SVG
Exibe preview do SVG com 3 fallbacks:
1. **Thumbnail**: Se `item.thumbnail` existe → usa imagem
2. **Inline**: Se `item.content` existe → data-URI base64
3. **Placeholder**: Mensagem "Sem prévia disponível"

#### Modal de Visualização (Alpine.js)
- Abre com botão "👁️ Visualizar"
- Fecha com ESC, click fora ou botão X
- Exibe SVG ampliado com `get_sanitized_content()`
- Transições suaves (fadeIn + slideUp)
- Acessível (ARIA, role="dialog")

#### Botão Copiar (HTMX)
- GET request para `core:copy_svg?id={{ item.pk }}`
- Copia SVG sanitizado para clipboard
- Feedback: "✓ Copiado!" por 2 segundos
- Tratamento de erro com try-catch

### Dependências

#### Alpine.js (CDN)
Requerido para funcionalidade do modal:
- x-data, x-show, x-cloak
- @click, @error
- x-teleport

#### HTMX (CDN)
Requerido para botão copiar:
- hx-get
- hx-swap
- hx-on::after-request

Ambos incluídos em `base.html`.

### Segurança

#### Sanitização
- Usa `item.get_sanitized_content()` que remove:
  - Tags `<script>`
  - Event handlers `onxxx`
- Preview via data-URI (não executa scripts)

**⚠️ Nota**: Sanitização mínima atual. Implementar whitelist robusta antes de produção pública.

#### CSP-Friendly
- Sem inline handlers (`onerror="..."`)
- Alpine.js directives em vez de JS inline
- HTMX attributes declarativos

### Estilização

Classes CSS (em `ui-enhancements.css`):
- `.card` - Container do card
- `.svg-thumb` - Preview area
- `.card-title` - Título
- `.card-description` - Descrição
- `.card-actions` - Container de botões
- `.btn`, `.btn-accent`, `.btn-secondary` - Botões
- `.modal-backdrop`, `.modal` - Modal
- `.modal-header`, `.modal-body` - Partes do modal

### Exemplo Completo

```django
{% load akka_filters %}

<div class="container-cards">
  {% for item in svgfiles %}
    {% include 'core/partials/item_card.html' %}
  {% endfor %}
</div>
```

### Acessibilidade

- ✅ ARIA labels em todos os botões
- ✅ `role="dialog"` e `aria-modal="true"` no modal
- ✅ `aria-labelledby` para título do modal
- ✅ Navegação via Tab
- ✅ Fechar com ESC
- ✅ Focus management

### Performance

- ✅ `loading="lazy"` em imagens
- ✅ Transitions GPU-accelerated
- ✅ Data-URI inline (sem request extra)
- ✅ x-cloak para evitar FOUC

### Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile: iOS 14+, Android Chrome 90+

Alpine.js e HTMX requerem browsers modernos com suporte a:
- ES6 Proxy
- MutationObserver
- Custom Elements
