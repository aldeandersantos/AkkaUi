# Guia de Configuração Stripe - Assinaturas Recorrentes

## ⚠️ IMPORTANTE: Configurar Price IDs no Stripe Dashboard

Para que as assinaturas funcionem corretamente, você precisa criar os **Products** e **Prices** no Stripe Dashboard.

## Passo a Passo

### 1. Acessar Stripe Dashboard
1. Acesse [https://dashboard.stripe.com/](https://dashboard.stripe.com/)
2. Faça login com sua conta Stripe

### 2. Criar Produtos e Preços

#### Plano Mensal (Pro Month)
1. No menu lateral, clique em **Products** → **Add Product**
2. Preencha:
   - **Name**: `AkkaUi Pro - Mensal`
   - **Description**: `Plano de assinatura mensal do AkkaUi`
   - **Pricing model**: `Standard pricing`
   - **Price**: `9.90` BRL
   - **Billing period**: `Monthly`
   - **Recurring**: ✅ Sim
3. Clique em **Save product**
4. **COPIE o Price ID** (formato: `price_xxxxxxxxxxxxx`)

#### Plano Anual (Pro Year)
1. Clique em **Add Product** novamente
2. Preencha:
   - **Name**: `AkkaUi Pro - Anual`
   - **Description**: `Plano de assinatura anual do AkkaUi com desconto`
   - **Pricing model**: `Standard pricing`
   - **Price**: `99.00` BRL
   - **Billing period**: `Yearly`
   - **Recurring**: ✅ Sim
3. Clique em **Save product**
4. **COPIE o Price ID** (formato: `price_xxxxxxxxxxxxx`)

### 3. Atualizar o Código

Após criar os preços no Stripe, você precisa atualizar o arquivo `templates/core/pricing.html`:

```javascript
// Linha ~682-687 em pricing.html
const stripePriceMap = {
  'monthly': 'price_xxxxxxxxxxxxx',  // ← Substitua pelo Price ID do plano mensal
  'annual': 'price_yyyyyyyyyyyyy'    // ← Substitua pelo Price ID do plano anual
};
```

**Exemplo:**
```javascript
const stripePriceMap = {
  'monthly': 'price_1ABCD1234567890',  // Price ID real do Stripe
  'annual': 'price_1EFGH9876543210'    // Price ID real do Stripe
};
```

## Como Funciona Agora

### Fluxo de Assinatura no Stripe

1. **Usuário escolhe plano** (Mensal ou Anual) na página `/pricing/`
2. **Clica em "Assinar"** e seleciona Stripe
3. **Mensagem de confirmação** aparece informando:
   - Valor da primeira cobrança
   - Data da próxima cobrança (30 dias para mensal, 365 para anual)
   - Que é uma assinatura recorrente
4. **Usuário confirma** e é redirecionado para `checkout.stripe.com`
5. **Preenche dados** do cartão no Stripe Checkout
6. **Webhook automático** do Stripe atualiza:
   - `user.is_vip = True`
   - `user.vip_expiration = data_da_proxima_cobranca`

### Renovação Automática

- **Stripe cobra automaticamente** todo mês (ou ano) no mesmo dia
- **Webhooks** do Stripe atualizam a `vip_expiration` automaticamente
- **Usuário vê** a próxima data de cobrança no perfil (`/usuario/profile/`)

### Cancelamento

- Usuário pode cancelar no **Stripe Customer Portal**
- Webhook `customer.subscription.deleted` é acionado
- Sistema atualiza automaticamente: `user.is_vip = False`

## Perfil do Usuário

O perfil agora mostra:

```
┌─────────────────────────────────────┐
│ Status: Assinante — até 30/09/2025  │
│                                      │
│ Informações da Assinatura           │
│ ┌─────────────────────────────────┐ │
│ │ Próxima cobrança: 30/09/2025    │ │
│ │                                 │ │
│ │ Sua assinatura será renovada... │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Diferença: Compra Única vs Assinatura

### Stripe - Assinatura (Pricing Page)
```
✅ Renovação automática
✅ Webhooks gerenciam VIP automaticamente
✅ Usuário vê próxima cobrança no perfil
✅ Usa /payment/stripe/checkout/ com mode=subscription
```

### Stripe - Compra Única (Checkout Page)
```
❌ Sem renovação
❌ Não gerencia VIP
✅ Usado para comprar SVGs avulsos
✅ Usa Checkout Session com mode=payment
```

## Testando

### Modo de Teste (Test Mode)
1. Use **cartões de teste** do Stripe:
   - `4242 4242 4242 4242` (sucesso)
   - Qualquer CVC, data futura
2. Webhook será processado normalmente
3. VIP será ativado automaticamente

### Modo de Produção (Live Mode)
1. Configure webhooks em produção:
   - URL: `https://seu-dominio.com/payment/stripe/djstripe/webhook/`
   - Eventos: `invoice.payment_succeeded`, `customer.subscription.*`
2. Use cartões reais
3. Stripe cobrará valores reais

## Resolução de Problemas

### "Plano não configurado no Stripe"
- Você não atualizou os Price IDs no código
- Solução: Copie os Price IDs do Dashboard e atualize `pricing.html`

### "VIP não foi ativado após pagamento"
- Webhook não foi configurado corretamente
- Solução: Verifique webhooks no Stripe Dashboard
- URL deve ser: `https://seu-dominio.com/payment/stripe/djstripe/webhook/`

### "Data de cobrança incorreta"
- Webhook `invoice.payment_succeeded` atualiza `vip_expiration`
- Verifique logs: `payment/signals.py`

## Suporte

Para mais informações sobre Stripe:
- [Stripe Subscriptions Documentation](https://stripe.com/docs/billing/subscriptions/overview)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
