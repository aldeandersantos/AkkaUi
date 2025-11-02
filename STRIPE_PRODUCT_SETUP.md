# Guia de Configuração: Produto Stripe AkkaUi Premium

## 🎯 Produto Criado no Stripe

**Product ID**: `prod_TLWbxxOkKwC4QD`  
**Nome**: AkkaUi Premium

## 📋 Estrutura de Preços

O produto possui 3 níveis de assinatura recorrente:

| Plano | Período | Preço | Economia |
|-------|---------|-------|----------|
| Mensal | 1 mês | US$ 6.99 | - |
| Trimestral | 3 meses | US$ 19.90 | ~5% |
| Anual | 12 meses | US$ 69.90 | ~15% |

## ⚙️ Passos para Configurar

### 1. Obter Price IDs do Stripe Dashboard

1. Acesse [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navegue para **Products** → **AkkaUi Premium** (`prod_TLWbxxOkKwC4QD`)
3. Na seção **Pricing**, você verá os 3 preços criados
4. Para cada preço, **copie o Price ID** (formato: `price_xxxxxxxxxxxxx`)

Exemplo do que você verá:
```
US$ 6.99 / month     → price_abc123monthly
US$ 19.90 / 3 months → price_def456quarterly  
US$ 69.90 / year     → price_ghi789annual
```

### 2. Atualizar o Código

Edite o arquivo `templates/core/pricing.html` na **linha ~720**:

```javascript
// Mapear planos para Stripe Price IDs do produto prod_TLWbxxOkKwC4QD
const stripePriceMap = {
  'monthly': 'price_abc123monthly',     // ← Cole o Price ID mensal aqui
  'quarterly': 'price_def456quarterly', // ← Cole o Price ID trimestral aqui
  'annual': 'price_ghi789annual'        // ← Cole o Price ID anual aqui
};
```

**⚠️ IMPORTANTE**: Substitua os valores de exemplo pelos Price IDs reais copiados do Stripe Dashboard.

### 3. Configurar Webhooks

Para que o sistema atualize automaticamente o status VIP dos usuários:

1. No Stripe Dashboard, vá para **Developers** → **Webhooks**
2. Clique em **Add endpoint**
3. Configure:
   - **Endpoint URL**: `https://seu-dominio.com/payment/stripe/djstripe/webhook/`
   - **Events to send**: 
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
4. Copie o **Signing secret** (formato: `whsec_xxxxxxxxxxxxx`)
5. Adicione ao arquivo `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

### 4. Configurar Chaves da API

No arquivo `.env` ou `env/.env`:

```env
# Stripe - Production
STRIPE_LIVE_MODE=True
STRIPE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_LIVE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Stripe - Test (para desenvolvimento)
STRIPE_TEST_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_TEST_SECRET_KEY=sk_test_xxxxxxxxxxxxx
```

## 🔄 Como Funciona

### Fluxo de Assinatura

1. **Usuário escolhe plano** na página `/pricing/`
2. **Clica em "Start Now"**
3. **Modal aparece** mostrando apenas Stripe (único gateway com suporte a assinaturas)
4. **Mensagem de confirmação** mostra:
   - Valor da primeira cobrança (US$ 6.99, 19.90 ou 69.90)
   - Data da próxima cobrança (calculada automaticamente)
   - Período de renovação (Mensal, Trimestral ou Anual)
5. **Usuário confirma** e é redirecionado para `checkout.stripe.com`
6. **Preenche dados** do cartão no Stripe Checkout
7. **Webhook do Stripe** notifica o sistema:
   - `user.is_vip = True`
   - `user.vip_expiration = data_da_proxima_cobranca`

### Renovação Automática

- **Stripe cobra automaticamente** no período definido:
  - Mensal: a cada 30 dias
  - Trimestral: a cada 90 dias
  - Anual: a cada 365 dias
- **Webhook `invoice.payment_succeeded`** atualiza `vip_expiration`
- **Usuário vê** no perfil (`/usuario/profile/`) quando será a próxima cobrança

### Cancelamento

- Usuário pode cancelar através do **Stripe Customer Portal**
- Webhook `customer.subscription.deleted` é acionado
- Sistema atualiza: `user.is_vip = False`, `user.vip_expiration = None`

## 📊 Perfil do Usuário

Após assinar, o perfil mostra:

```
┌─────────────────────────────────────┐
│ Status: Assinante — até 15/12/2025  │
│                                      │
│ Informações da Assinatura           │
│ ┌─────────────────────────────────┐ │
│ │ Próxima cobrança: 15/12/2025    │ │
│ │                                 │ │
│ │ Sua assinatura será renovada... │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🛍️ Compras Únicas (Checkout Page)

Para compras avulsas de SVGs, o sistema ainda suporta:
- **AbacatePay**: PIX (pagamento único)
- **Mercado Pago**: Cartão/Boleto (pagamento único)
- **Stripe**: Cartão internacional (pagamento único)

Estes são usados na página `/checkout/` para compras de SVGs individuais.

## 🎨 Diferença: Pricing vs Checkout

| Página | Uso | Gateways | Tipo |
|--------|-----|----------|------|
| **/pricing/** | Assinaturas VIP | **Stripe apenas** | Recorrente |
| **/checkout/** | Compra de SVGs | AbacatePay, Mercado Pago, Stripe | Único |

## 🧪 Testando

### Modo de Teste

1. Use `STRIPE_LIVE_MODE=False` no `.env`
2. Use cartões de teste do Stripe:
   - `4242 4242 4242 4242` (sucesso)
   - `4000 0000 0000 0002` (falha)
   - Qualquer CVC válido (ex: 123)
   - Qualquer data futura
3. Webhook funcionará normalmente
4. VIP será ativado após "pagamento"

### Modo de Produção

1. Configure `STRIPE_LIVE_MODE=True`
2. Use chaves de produção (`pk_live_*`, `sk_live_*`)
3. Configure webhook em produção
4. Cartões reais serão cobrados

## 🔧 Resolução de Problemas

### "Plano não configurado no Stripe"
- **Causa**: Price IDs não atualizados no código
- **Solução**: Copie os Price IDs do Dashboard e atualize linha ~720 em `pricing.html`

### "VIP não ativado após pagamento"
- **Causa**: Webhook não configurado ou não processado
- **Solução**: 
  1. Verifique URL do webhook: `https://seu-dominio.com/payment/stripe/djstripe/webhook/`
  2. Verifique logs do Django: `python manage.py runserver` ou logs de produção
  3. Verifique no Stripe Dashboard → Webhooks → Logs de eventos

### "Próxima cobrança incorreta"
- **Causa**: Webhook não atualizando `vip_expiration`
- **Solução**: Verifique `payment/signals.py` e logs de processamento de webhook

### Checklist de Configuração

- [ ] Product ID confirmado: `prod_TLWbxxOkKwC4QD`
- [ ] 3 Price IDs copiados do Stripe Dashboard
- [ ] Price IDs atualizados em `pricing.html` linha ~720
- [ ] Chaves da API configuradas no `.env`
- [ ] Webhook configurado no Stripe Dashboard
- [ ] Webhook secret adicionado ao `.env`
- [ ] Testado em modo de teste
- [ ] Migrado para produção

## 📚 Recursos Adicionais

- [Stripe Subscriptions](https://stripe.com/docs/billing/subscriptions/overview)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [dj-stripe Documentation](https://dj-stripe.readthedocs.io/)

## 💡 Dicas

1. **Sempre teste em modo de teste** antes de ir para produção
2. **Monitore os webhooks** no Stripe Dashboard para debugar problemas
3. **Use diferentes e-mails** ao testar para simular múltiplos clientes
4. **Cancele assinaturas de teste** para não acumular dados desnecessários
5. **Documente os Price IDs** em um local seguro (gerenciador de senhas)

---

**Última atualização**: 02/11/2025  
**Produto Stripe**: `prod_TLWbxxOkKwC4QD`  
**Status**: ✅ Configuração pronta para uso
