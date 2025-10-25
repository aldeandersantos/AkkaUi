# Documentação da API de Carrinho de Compras

## Visão Geral

O sistema de pagamento agora suporta compras de múltiplos itens em uma única transação, funcionando como um carrinho de compras. É possível comprar:
- Planos de assinatura (VIP)
- Arquivos SVG individuais
- Combinação de planos e SVGs

## Compatibilidade

A API mantém 100% de compatibilidade com o código existente. Chamadas antigas continuam funcionando normalmente.

## Endpoints

### POST `/payment/create/`

Cria um novo pagamento. Suporta dois modos:

#### Modo Legado (Plano Único)

**Request:**
```json
{
  "gateway": "abacatepay",
  "plan": "pro_month",
  "currency": "BRL"
}
```

**Response:**
```json
{
  "status": "success",
  "payment": {
    "transaction_id": "abc123...",
    "gateway": "abacatepay",
    "plan": "pro_month",
    "amount": "9.90",
    "currency": "BRL",
    "status": "pending",
    "gateway_payment_id": "gw_123",
    "gateway_response": {...},
    "items": [],
    "created_at": "2025-10-25T04:00:00Z"
  }
}
```

**Nota:** No modo legado, o campo `items` é uma lista vazia, pois o item é representado diretamente no campo `plan`.

#### Modo Carrinho (Múltiplos Itens)

**Request:**
```json
{
  "gateway": "abacatepay",
  "items": [
    {"type": "svg", "id": 1, "quantity": 2},
    {"type": "svg", "id": 3, "quantity": 1},
    {"type": "plan", "id": "pro_month", "quantity": 1}
  ],
  "currency": "BRL"
}
```

**Response:**
```json
{
  "status": "success",
  "payment": {
    "transaction_id": "xyz789...",
    "gateway": "abacatepay",
    "plan": null,
    "amount": "54.90",
    "currency": "BRL",
    "status": "pending",
    "gateway_payment_id": "gw_456",
    "gateway_response": {...},
    "items": [
      {
        "type": "svg",
        "name": "Logo Premium",
        "quantity": 2,
        "unit_price": "10.00",
        "total_price": "20.00"
      },
      {
        "type": "svg",
        "name": "Icon Set",
        "quantity": 1,
        "unit_price": "25.00",
        "total_price": "25.00"
      },
      {
        "type": "plan",
        "name": "pro_month",
        "quantity": 1,
        "unit_price": "9.90",
        "total_price": "9.90"
      }
    ],
    "created_at": "2025-10-25T04:00:00Z"
  }
}
```

**Nota:** No modo carrinho, `plan` é `null` indicando que é um pagamento baseado em carrinho com múltiplos itens. Os detalhes de cada item estão no array `items`.

## Estrutura de Items

Cada item no carrinho deve ter:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | string | Tipo do item: `"plan"` ou `"svg"` |
| `id` | int ou string | Para SVG: ID numérico (ex: `123`). Para plan: string com nome (ex: `"pro_month"`) |
| `quantity` | int | Quantidade (opcional, padrão: 1). Para planos, sempre será 1 independente do valor enviado |

**Importante:** O tipo do campo `id` varia conforme o tipo do item:
- SVG: integer (ex: `1`, `42`, `123`)
- Plan: string (ex: `"pro_month"`, `"pro_year"`)

### Tipos de Item

#### SVG
```json
{"type": "svg", "id": 123, "quantity": 2}
```
- `id`: **Integer** - ID do SvgFile no banco de dados
- O SVG deve ter `price > 0` para ser vendável
- O preço é obtido do campo `price` do modelo SvgFile
- Quantity pode ser qualquer valor positivo

#### Plano
```json
{"type": "plan", "id": "pro_month", "quantity": 1}
```
- `id`: **String** - Nome do plano (pro_month, pro_year, enterprise_month, enterprise_year)
- **Quantidade sempre será 1 para planos** (valor enviado é ignorado)
- Preço é obtido da configuração `PaymentService.PLAN_PRICES`

## Validações

O sistema valida:
- ✓ Gateway suportado
- ✓ Lista de items não vazia (quando presente)
- ✓ SVG existe no banco de dados
- ✓ SVG tem preço > 0 (vendável)
- ✓ Plano é válido
- ✓ **Para planos: quantidade é sempre fixada em 1** (não é possível comprar múltiplos planos na mesma transação)

## Erros

### Erros Comuns

**Gateway não suportado:**
```json
{
  "error": "unsupported_gateway"
}
```

**Items vazio:**
```json
{
  "error": "items_must_be_non_empty_list"
}
```

**SVG não encontrado:**
```json
{
  "status": "error",
  "error": "SVG 999 não encontrado"
}
```

**SVG não vendável (preço = 0):**
```json
{
  "status": "error",
  "error": "SVG 123 não está disponível para venda"
}
```

## Exemplo Completo de Uso

### JavaScript (Frontend)

```javascript
// Carrinho do cliente
const cart = [
  { type: 'svg', id: 1, quantity: 2 },
  { type: 'svg', id: 3, quantity: 1 },
  { type: 'plan', id: 'pro_month', quantity: 1 }
];

// Criar pagamento
const response = await fetch('/payment/create/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({
    gateway: 'abacatepay',
    items: cart,
    currency: 'BRL'
  })
});

const data = await response.json();

if (data.status === 'success') {
  console.log('Pagamento criado:', data.payment.transaction_id);
  console.log('Total:', data.payment.amount);
  console.log('Items:', data.payment.items);
  
  // Redirecionar para gateway de pagamento se necessário
  if (data.payment.gateway_response.payment_url) {
    window.location.href = data.payment.gateway_response.payment_url;
  }
} else {
  console.error('Erro:', data.error);
}
```

### Python (Backend)

```python
from payment.services.payment_service import PaymentService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='cliente')

# Criar pagamento com carrinho
items = [
    {'type': 'svg', 'id': 1, 'quantity': 2},
    {'type': 'svg', 'id': 3, 'quantity': 1},
    {'type': 'plan', 'id': 'pro_month', 'quantity': 1}
]

payment = PaymentService.create_payment_with_items(
    user=user,
    gateway_name='abacatepay',
    items=items,
    currency='BRL'
)

print(f"Pagamento criado: {payment.transaction_id}")
print(f"Total: R$ {payment.amount}")
print(f"Items: {payment.items.count()}")
```

## Modelos

### Payment
- `plan`: Agora é opcional (null para pagamentos de carrinho)
- `amount`: Total do pagamento (soma de todos os items)

### PaymentItem (Novo)
- `payment`: ForeignKey para Payment
- `item_type`: 'plan' ou 'svg'
- `item_id`: ID do item
- `quantity`: Quantidade comprada
- `unit_price`: Preço unitário
- `total_price`: Calculado automaticamente (unit_price × quantity)
- `item_name`: Nome do item (para referência)
- `item_metadata`: Metadados adicionais (JSON)

### SvgFile
- `price`: Novo campo para preço de venda (Decimal)
  - Default: 0.00 (gratuito)
  - Apenas SVGs com price > 0 são vendáveis

## Aplicação de VIP

Quando um pagamento é confirmado:
- Se contém um plano: VIP é aplicado ao usuário
- Se contém apenas SVGs: VIP não é aplicado
- O período VIP é calculado baseado no plano (mensal ou anual)

## Próximos Passos

Para integração completa, considere:
1. Criar interface de carrinho no frontend
2. Adicionar botão "Adicionar ao carrinho" nos SVGs
3. Mostrar resumo do carrinho antes do checkout
4. Implementar histórico de compras com detalhes dos items
5. Adicionar filtros na listagem de SVGs por preço
