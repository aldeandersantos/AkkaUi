# SvgAsset Model - Documentação

## Visão Geral

O modelo `SvgAsset` foi criado para armazenar e gerenciar arquivos SVG de forma segura no app `core` do projeto AkkaUi. O modelo implementa sanitização automática de conteúdo SVG para prevenir ataques XSS (Cross-Site Scripting).

## Características

### Campos do Modelo

- **nome** (CharField): Nome identificador do asset SVG
- **svg_text** (TextField): Markup SVG sanitizado (armazenado como texto)
- **svg_file** (FileField): Arquivo SVG opcional (armazenado em `media/svgs/`)
- **descricao** (TextField): Descrição opcional do SVG
- **tags** (TextField): Tags separadas por vírgula para categorização
- **data_criacao** (DateTimeField): Data de criação (automático)
- **data_atualizacao** (DateTimeField): Data da última atualização (automático)

### Sanitização de Segurança

O modelo implementa sanitização automática usando a biblioteca `bleach` para:

1. **Remover tags perigosas**: Tags `<script>` e outras tags não permitidas são removidas
2. **Remover atributos perigosos**: Atributos de eventos JavaScript como `onclick`, `onload`, `onerror`, etc. são removidos
3. **Preservar tags SVG válidas**: Apenas tags SVG legítimas são mantidas (circle, path, rect, g, etc.)

#### Tags SVG Permitidas

```python
'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
'text', 'tspan', 'tref', 'textPath', 'defs', 'linearGradient', 'radialGradient',
'stop', 'pattern', 'clipPath', 'mask', 'use', 'symbol', 'marker', 'title', 'desc',
'metadata', 'foreignObject', 'image', 'animate', 'animateTransform', 'animateMotion',
'set', 'filter', [elementos de filtro SVG...]
```

### Comportamento Automático

#### Ao Salvar com `svg_text`
```python
svg = SvgAsset.objects.create(
    nome="Meu SVG",
    svg_text="<svg>...</svg>"
)
# O svg_text é automaticamente sanitizado
```

#### Ao Salvar com `svg_file`
```python
from django.core.files.uploadedfile import SimpleUploadedFile

svg_file = SimpleUploadedFile("icon.svg", svg_content.encode('utf-8'))
svg = SvgAsset.objects.create(
    nome="Ícone",
    svg_file=svg_file
)
# O conteúdo do arquivo é lido, sanitizado e armazenado em svg_text
```

## Uso

### No Django Admin

O modelo está registrado no Django Admin com interface completa:

1. Acesse `/admin/core/svgasset/`
2. Clique em "Add SVG Asset"
3. Preencha os campos:
   - Nome (obrigatório)
   - SVG Markup ou arquivo (pelo menos um)
   - Descrição e tags (opcionais)

### Programaticamente

```python
from core.models import SvgAsset

# Criar com texto
svg = SvgAsset.objects.create(
    nome="Logo",
    svg_text="""<svg viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="blue"/>
    </svg>""",
    tags="logo, circle, blue"
)

# Buscar SVGs
all_svgs = SvgAsset.objects.all()
logo_svgs = SvgAsset.objects.filter(tags__icontains="logo")

# Atualizar
svg.descricao = "Logo principal da empresa"
svg.save()
```

## Segurança

### Proteção contra XSS

O modelo protege contra os seguintes vetores de ataque:

❌ **Bloqueado**: `<script>alert('XSS')</script>`
❌ **Bloqueado**: `<circle onclick="alert('XSS')"/>`
❌ **Bloqueado**: `<image onload="alert('XSS')"/>`
✅ **Permitido**: `<circle cx="50" cy="50" r="40" fill="red"/>`

### Testes de Segurança

Execute os testes para verificar a segurança:

```bash
python manage.py test core
```

Todos os testes incluem verificações de sanitização.

## Requisitos

- Django 5.2+
- bleach 6.2+
- Pillow 12.0+ (para upload de arquivos)

## Configuração

### settings.py

```python
INSTALLED_APPS = [
    ...
    'core',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Migrations

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Limitações Conhecidas

1. Apenas SVG markup é suportado (não converte outros formatos)
2. Tags SVG permitidas são limitadas à lista pré-definida
3. Arquivo SVG deve ser UTF-8

## Desenvolvimento Futuro

Possíveis melhorias:
- [ ] Otimização automática de SVG (remoção de metadados desnecessários)
- [ ] Validação de SVG bem-formado
- [ ] Geração automática de miniaturas
- [ ] Suporte para múltiplas versões (otimizado/original)
- [ ] API REST para gerenciamento de SVGs
