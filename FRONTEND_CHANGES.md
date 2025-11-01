# Mudanças no Frontend - PayPal → Stripe

## Resumo
Substituído todas as referências de "PayPal" por "Stripe" nos templates HTML do frontend.

## Arquivos Modificados

### 1. `templates/core/checkout.html` (Linha 51-57)

**ANTES:**
```html
<label style="...">
  <input type="radio" name="gateway" value="paypal" ...>
  <div>
    <div style="...">PayPal</div>
    <div class="muted" style="...">Pagamento internacional</div>
  </div>
</label>
```

**DEPOIS:**
```html
<label style="...">
  <input type="radio" name="gateway" value="stripe" ...>
  <div>
    <div style="...">Stripe</div>
    <div class="muted" style="...">Cartão de crédito internacional</div>
  </div>
</label>
```

**Impacto Visual:**
- Terceira opção de pagamento agora mostra "Stripe" ao invés de "PayPal"
- Descrição atualizada para "Cartão de crédito internacional"
- O valor do radio button agora é `value="stripe"` que é reconhecido pelo backend

---

### 2. `templates/core/pricing.html` (Linha 446-450)

**ANTES:**
```html
<button class="payment-method" onclick="selectGateway('paypal')">
  <div class="method-icon">🌐</div>
  <div class="method-name">PayPal</div>
  <div class="method-description">Pagamento internacional (em breve)</div>
</button>
```

**DEPOIS:**
```html
<button class="payment-method" onclick="selectGateway('stripe')">
  <div class="method-icon">💳</div>
  <div class="method-name">Stripe</div>
  <div class="method-description">Cartão de crédito internacional</div>
</button>
```

**Impacto Visual:**
- Modal de seleção de pagamento agora mostra "Stripe" como terceira opção
- Ícone mudou de 🌐 (globo) para 💳 (cartão)
- Descrição atualizada para "Cartão de crédito internacional"
- JavaScript chama `selectGateway('stripe')` ao invés de `selectGateway('paypal')`
- Removido "(em breve)" da descrição já que Stripe está funcional

---

## Como Testar

### Página de Checkout (`/checkout/`)
1. Adicione itens ao carrinho
2. Vá para o checkout
3. Verifique que a terceira opção agora é "Stripe" com descrição "Cartão de crédito internacional"
4. Selecione Stripe e clique em "Complete Purchase"
5. Backend deve processar com `gateway="stripe"`

### Página de Preços (`/pricing/`)
1. Acesse a página de preços
2. Clique em "Start Now" em um dos planos pagos
3. No modal de seleção de pagamento, verifique:
   - Primeira opção: "PIX via Abacate Pay"
   - Segunda opção: "Mercado Pago"
   - Terceira opção: "Stripe" (NOVO - antes era PayPal)
4. Ao clicar em Stripe, deve criar pagamento com `gateway="stripe"`

---

## Visão Geral das Três Formas de Pagamento

### No Checkout:
```
┌─────────────────────────────────────┐
│  Payment Method                     │
├─────────────────────────────────────┤
│  ○ Abacate Pay                      │
│    Pagamento via PIX                │
├─────────────────────────────────────┤
│  ○ Mercado Pago                     │
│    Cartão, PIX, Boleto              │
├─────────────────────────────────────┤
│  ○ Stripe                   (NOVO)  │
│    Cartão de crédito internacional  │
└─────────────────────────────────────┘
```

### No Modal de Pricing:
```
┌─────────────────────────────────────┐
│  Selecione a forma de pagamento     │
├─────────────────────────────────────┤
│  [💳 PIX via Abacate Pay]           │
│  Pagamento instantâneo via PIX      │
├─────────────────────────────────────┤
│  [💰 Mercado Pago]                  │
│  Cartão, boleto e mais              │
├─────────────────────────────────────┤
│  [💳 Stripe]                (NOVO)  │
│  Cartão de crédito internacional    │
└─────────────────────────────────────┘
```

---

## Benefícios da Mudança

✅ **Funcionalidade Real**: Stripe está implementado e funcional (PayPal era apenas stub)

✅ **Consistência**: Frontend agora alinhado com backend que já tem StripeGateway

✅ **Integração Completa**: 
- Compras únicas de SVG funcionam via `/payment/create/` com `gateway="stripe"`
- Assinaturas funcionam via `/payment/stripe/checkout/` com `mode="subscription"`

✅ **UX Melhorada**: Descrição clara "Cartão de crédito internacional" vs vago "Pagamento internacional"

---

## Compatibilidade Backend

O backend já está preparado para receber `gateway="stripe"`:

```python
# payment/models.py
GATEWAY_CHOICES = [
    ('abacatepay', 'Abacate Pay'),
    ('mercadopago', 'Mercado Pago'),
    ('stripe', 'Stripe'),  # ✅ Pronto
]

# payment/services/payment_service.py
GATEWAY_MAP = {
    'abacatepay': AbacatePayGateway,
    'mercadopago': MercadoPagoGateway,
    'stripe': StripeGateway,  # ✅ Implementado
}
```

Quando o usuário seleciona Stripe no frontend:
1. JavaScript envia `POST /payment/create/` com `{"gateway": "stripe", ...}`
2. Backend usa `StripeGateway` para processar
3. Stripe Payment Intent é criado
4. Usuário é direcionado para checkout do Stripe
5. Após pagamento, webhooks atualizam status automaticamente

---

**Commit:** Próximo commit após validação
**Status:** ✅ Pronto para teste
