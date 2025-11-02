# 🚀 Setup Rápido - Stripe Price IDs

## ⚠️ IMPORTANTE: Configuração Obrigatória

O sistema está configurado para usar o produto **`prod_TLWbxxOkKwC4QD`** do Stripe, mas os Price IDs ainda precisam ser inseridos no código.

## 📋 Passo a Passo (5 minutos)

### 1. Acesse seu Stripe Dashboard

🔗 [https://dashboard.stripe.com/products/prod_TLWbxxOkKwC4QD](https://dashboard.stripe.com/products/prod_TLWbxxOkKwC4QD)

### 2. Copie os 3 Price IDs

Na página do produto, você verá 3 preços. Copie o **ID** de cada um:

```
✅ US$ 6.99 / mês     → price_abc123xxx (exemplo)
✅ US$ 19.90 / 3 meses → price_def456xxx (exemplo)
✅ US$ 69.90 / ano    → price_ghi789xxx (exemplo)
```

**Importante**: Os Price IDs sempre começam com `price_` seguido de caracteres aleatórios.

### 3. Atualize o Código

Abra o arquivo: **`templates/core/pricing.html`**

Procure pela **linha ~720** e substitua:

```javascript
// ANTES (placeholders - não funcionam)
const stripePriceMap = {
  'monthly': 'price_monthly_id',     // ❌ Placeholder
  'quarterly': 'price_quarterly_id', // ❌ Placeholder
  'annual': 'price_annual_id'        // ❌ Placeholder
};

// DEPOIS (seus Price IDs reais)
const stripePriceMap = {
  'monthly': 'price_abc123xxx',      // ✅ Cole seu Price ID mensal aqui
  'quarterly': 'price_def456xxx',    // ✅ Cole seu Price ID trimestral aqui
  'annual': 'price_ghi789xxx'        // ✅ Cole seu Price ID anual aqui
};
```

### 4. Salve e Teste

Acesse `/pricing/` e tente assinar um plano. Agora deve funcionar! 🎉

## 🔍 Como Identificar Price IDs no Dashboard

1. Vá para **Products** → **AkkaUi Premium**
2. Na seção **Preços**, cada linha tem:
   - Preço (ex: US$ 6.99)
   - Frequência (ex: Monthly)
   - **ID** (ex: `price_1ABC123xyz`) ← Este é o que você precisa!

## ❓ Problemas Comuns

### Erro: "Price ID inválido"
✅ **Solução**: Verifique se você copiou o Price ID completo (começa com `price_`)

### Erro: "No such price"
✅ **Solução**: O Price ID pode estar de outro produto ou ambiente (test/live)

### Erro: "Invalid API Key"
✅ **Solução**: Configure as variáveis de ambiente:
   - `STRIPE_TEST_SECRET_KEY=sk_test_...`
   - `STRIPE_LIVE_SECRET_KEY=sk_live_...`

## 📚 Documentação Completa

Para mais detalhes, veja: **`STRIPE_PRODUCT_SETUP.md`**

## 🎯 Resultado Esperado

Após configurar, ao clicar em "Assinar" na pricing page:

1. ✅ Modal de confirmação aparece
2. ✅ Mostra próxima data de cobrança
3. ✅ Redireciona para checkout.stripe.com
4. ✅ VIP é ativado automaticamente após pagamento

---

**Need help?** Check the error message - the system now provides detailed feedback!
