# Frontend UI Update - Testing Guide

## Objetivo
Este PR atualiza o frontend do AkkaUi com um layout moderno inspirado em uiwiki.co, usando HTMX e Alpine.js via CDN.

## Como testar localmente

### 1. Configurar ambiente
```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar banco de dados
```bash
# Criar migrations (se necessário)
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Criar usuário de teste
python manage.py shell
>>> from usuario.models import CustomUser
>>> user = CustomUser.objects.create_user('test', 'test@test.com', 'test123', admin=True)
>>> exit()
```

### 3. Criar dados de teste (opcional)
```bash
python manage.py shell << 'EOF'
from usuario.models import CustomUser
from core.models import SvgFile

user = CustomUser.objects.first()

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="#7460F3"/>
</svg>'''

SvgFile.objects.create(
    title_name='Test SVG',
    description='Um SVG de teste',
    content=svg_content,
    owner=user,
    is_public=True
)
EOF
```

### 4. Rodar servidor
```bash
python manage.py runserver
```

### 5. Acessar e testar
- Abrir navegador em http://localhost:8000/
- Verificar grid de cards responsivo
- Testar hover animations nos cards
- Clicar em "Visualizar" para abrir modal (requer Alpine.js)
- Clicar em "Copiar" para copiar SVG (requer HTMX)
- Redimensionar janela para testar responsividade

## Funcionalidades implementadas

### Grid Responsivo
- Desktop: múltiplas colunas (auto-fill, min 300px)
- Mobile: coluna única
- Gap de 24px (desktop) / 16px (mobile)

### Cards
- Preview de SVG (thumbnail, inline ou placeholder)
- Título e descrição truncada
- Hover: translateY(-4px) + shadow
- Animações suaves (0.3s ease)

### Modal (Alpine.js)
- Abre com botão "Visualizar"
- Fecha com ESC, click fora ou botão X
- Transitions suaves (fadeIn + slideUp)
- Preview ampliado do SVG
- Acessível (role="dialog", aria-modal)

### Botão Copiar (HTMX)
- GET request para /api/copy_svg/?id=X
- Copia SVG sanitizado para clipboard
- Feedback visual ("✓ Copiado!" por 2s)
- Tratamento de erros

## Segurança

### Sanitização de SVG
- `get_sanitized_content()` remove &lt;script&gt; tags
- Remove event handlers (onxxx="...")
- Preview via data-URI base64 (não executa scripts)

### CDN Integrity
- HTMX 1.9.10 com SHA-384 integrity check
- Alpine.js 3.13.5 com SHA-384 integrity check
- crossorigin="anonymous"

### Tratamento de Erros
- JSON.parse com try-catch
- Alpine @error para fallback de imagens
- Exceções específicas em Python

## Paleta de Cores Mantida

- `--accent: #7460F3` (roxo primário)
- `--bg-dark: #0c0c0c` (fundo escuro)
- `--bg-card: #1a1a1a` (cards)
- `--text-light: #e7e7e7` (texto claro)
- `--text-muted: #7b7b7b` (texto secundário)
- `--border: #2a2a2a` (bordas)

## Arquivos Modificados

### Criados
- `static/core/ui-enhancements.css` - Estilos novos
- `core/templatetags/akka_filters.py` - Filtro base64
- `templates/core/partials/item_card.html` - Card reutilizável

### Atualizados
- `templates/core/base.html` - CDNs + CSS
- `templates/core/home.html` - Grid de cards

## Troubleshooting

### CDN bloqueado
Se HTMX ou Alpine.js não carregarem (ERR_BLOCKED_BY_CLIENT):
- Desabilitar ad-blockers/extensions
- Verificar CSP headers
- Testar em navegador anônimo

### Modal não abre
- Verificar console do navegador
- Confirmar Alpine.js carregado
- Verificar x-data no card

### Copiar não funciona
- Verificar HTMX carregado
- Testar endpoint /api/copy_svg/ manualmente
- Verificar HTTPS (clipboard requer contexto seguro)

### Preview não aparece
- Verificar get_sanitized_content() retorna SVG válido
- Testar base64_encode no shell Django
- Verificar data-URI no inspector

## Performance

- Lazy loading de imagens (loading="lazy")
- Transitions otimizadas (GPU-accelerated)
- Media query prefers-reduced-motion
- Grid com auto-fill (não fixa quantidade)

## Compatibilidade

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile: iOS 14+, Android Chrome 90+

## Próximos Passos

1. Adicionar paginação se muitos SVGs
2. Implementar filtros/busca no grid
3. Adicionar tags visuais nos cards
4. Melhorar sanitização com whitelist robusta
5. Adicionar testes automatizados
