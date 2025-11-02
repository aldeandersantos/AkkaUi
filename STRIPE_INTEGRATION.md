# Integração Stripe - Sistema de Assinaturas VIP e Compras Únicas

## Visão Geral

Este sistema integra o gateway de pagamento Stripe ao aplicativo Django usando o pacote `dj-stripe`, permitindo tanto **cobranças recorrentes (assinaturas)** quanto **compras únicas de SVGs**.

## Como Funciona Agora: 3 Formas de Pagamento

O sistema agora suporta **três métodos de pagamento**:

### 1. **AbacatePay** (PIX - Apenas Compras Únicas)
- Gateway brasileiro para pagamentos via PIX
- **Usado apenas para compras únicas de SVGs**
- ❌ Não suporta assinaturas recorrentes (limitação do PIX)
- Webhooks em: `/payment/webhook/abacatepay/`

### 2. **Mercado Pago** (Compras Únicas e Assinaturas)
- Gateway latino-americano
- ✅ **Usado para compras únicas de SVGs**
- ✅ **Suporta assinaturas recorrentes**
- Webhooks em: `/payment/webhook/mercadopago/`

### 3. **Stripe** (NOVO - Compras Únicas e Assinaturas)
- Gateway internacional
- ✅ **Usado para compras únicas de SVGs**
- ✅ **Assinaturas VIP recorrentes (mensal/anual)**
- Atualiza automaticamente o status `is_vip` e `vip_expiration` do usuário
- Webhooks gerenciados pelo dj-stripe em: `/payment/stripe/` e `/payment/stripe/webhook/`

## Arquitetura da Solução Stripe

### 1. Modelos Utilizados

O dj-stripe cria e gerencia automaticamente modelos para:
- **Customer**: Cliente Stripe vinculado ao `CustomUser`
- **Subscription**: Assinatura recorrente do cliente
- **Invoice**: Faturas geradas automaticamente
- **Price**: Preços dos planos de assinatura
- **Event**: Eventos de webhook recebidos do Stripe

### 2. Fluxo de Assinatura

```
1. Usuário solicita checkout de assinatura
   ↓
2. Sistema cria/obtém Customer no Stripe (via get_or_create_stripe_customer)
   ↓
3. Cria sessão de checkout com Stripe Checkout
   ↓
4. Usuário preenche dados de pagamento no Stripe
   ↓
5. Stripe processa pagamento e cria Subscription
   ↓
6. Stripe envia webhook invoice.payment_succeeded
   ↓
7. Sistema atualiza user.is_vip = True e user.vip_expiration
```

### 3. Webhooks e Sinais (payment/signals.py)

O sistema escuta os seguintes eventos do Stripe:

#### **invoice.payment_succeeded**
- Dispara quando uma fatura é paga com sucesso
- **Ação**: Define `is_vip = True` e atualiza `vip_expiration` com base no `current_period_end`

#### **customer.subscription.deleted**
- Dispara quando uma assinatura é cancelada
- **Ação**: Define `is_vip = False` e `vip_expiration = None`

#### **customer.subscription.updated**
- Dispara quando uma assinatura muda de status
- **Ações**:
  - Se status = `active` ou `trialing`: Define `is_vip = True`
  - Se status = `canceled`, `unpaid` ou `incomplete_expired`: Define `is_vip = False`

### 4. Endpoints da API

#### **POST /payment/stripe/checkout/**
Cria uma sessão de checkout do Stripe (assinaturas ou compras únicas).

**Request para Assinatura:**
```json
{
  "mode": "subscription",
  "price_id": "price_1ABC123...",
  "success_url": "http://exemplo.com/success",
  "cancel_url": "http://exemplo.com/cancel"
}
```

**Request para Compra Única:**
```json
{
  "mode": "payment",
  "currency": "BRL",
  "items": [
    {
      "name": "SVG Premium",
      "description": "Arquivo SVG de alta qualidade",
      "unit_price": 5.00,
      "quantity": 1
    }
  ],
  "success_url": "http://exemplo.com/success",
  "cancel_url": "http://exemplo.com/cancel"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_...",
  "mode": "subscription" | "payment"
}
```

#### **GET /payment/stripe/prices/**
Lista os preços de assinatura disponíveis.

**Response:**
```json
{
  "prices": [
    {
      "id": "price_123",
      "product": "Pro Mensal",
      "amount": 29.90,
      "currency": "brl",
      "interval": "month",
      "interval_count": 1
    }
  ]
}
```

#### **GET /payment/stripe/subscription-status/**
Retorna o status da assinatura do usuário logado.

**Response:**
```json
{
  "is_vip": true,
  "vip_expiration": "2025-12-01",
  "subscriptions": [
    {
      "id": "sub_123",
      "status": "active",
      "current_period_end": "2025-12-01T00:00:00",
      "cancel_at_period_end": false
    }
  ]
}
```

## Configuração Necessária

### 1. Variáveis de Ambiente (.env)

```env
# Stripe - Chaves de Teste
STRIPE_TEST_PUBLIC_KEY=pk_test_...
STRIPE_TEST_SECRET_KEY=sk_test_...

# Stripe - Chaves de Produção
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...

# Modo (True para produção, False para teste)
STRIPE_LIVE_MODE=False

# Webhook Secret (obtido no dashboard do Stripe)
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Configuração do Webhook no Stripe Dashboard

1. Acesse o [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. Clique em "Add endpoint"
3. URL: `https://seu-dominio.com/payment/stripe/djstripe/webhook/`
4. Eventos a escutar:
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
5. Copie o "Signing secret" e adicione em `STRIPE_WEBHOOK_SECRET`

### 3. Criar Produtos e Preços no Stripe

Pelo Stripe Dashboard:
1. Vá em "Products" → "Add product"
2. Crie produtos como "Pro Mensal", "Pro Anual"
3. Configure preços recorrentes (mensal, anual)
4. Copie os `price_id` para usar no checkout

## Sincronização de Dados

### Função: `get_or_create_stripe_customer(user)`
Localização: `payment/services/stripe_service.py`

```python
# Cria ou obtém Customer do Stripe para o usuário
customer = get_or_create_stripe_customer(request.user)
```

- Associa automaticamente o `CustomUser` ao `Customer` do Stripe
- Sincroniza email e nome do usuário

## Comparação dos Métodos de Pagamento

| Característica | AbacatePay | Mercado Pago | Stripe |
|----------------|------------|--------------|--------|
| **Tipo** | Único (PIX) | Único + Assinatura | Único + Assinatura |
| **Uso Primário** | Compra SVGs | Compra SVGs + VIP | Compra SVGs + VIP |
| **Região** | Brasil | América Latina | Internacional |
| **Atualiza VIP?** | ❌ Não | ✅ Sim (manual) | ✅ Sim (automático) |
| **Webhooks** | Manual | Manual | Automático (dj-stripe) |
| **Renovação** | ❌ Não | ✅ Sim | ✅ Automática |
| **Compras Únicas** | ✅ Sim | ✅ Sim | ✅ Sim |

## Modelo de Dados: CustomUser

```python
class CustomUser(AbstractUser):
    is_vip = models.BooleanField(default=False)
    vip_expiration = models.DateField(blank=True, null=True)
    # ... outros campos
```

**Atualização automática pelo Stripe:**
- Quando pagamento é aprovado: `is_vip = True`, `vip_expiration` = data do fim do período
- Quando assinatura é cancelada: `is_vip = False`, `vip_expiration = None`

## Testes

Foram criados 6 testes em `payment/test_stripe.py`:

1. ✅ Criação de Customer Stripe
2. ✅ Sincronização de usuário com Stripe
3. ✅ Criação de sessão de checkout
4. ✅ Status de assinatura do usuário
5. ✅ Atualização VIP após pagamento bem-sucedido
6. ✅ Remoção VIP após cancelamento

Execute com:
```bash
python manage.py test payment.test_stripe
```

## Fluxo Completo de Integração Frontend

### Exemplo: Página de Assinatura

```html
<!-- Template: subscription.html -->
<div id="subscription-plans">
    <div class="plan">
        <h3>Pro Mensal</h3>
        <p>R$ 29,90/mês</p>
        <button onclick="checkout('price_mensal_id')">Assinar</button>
    </div>
    <div class="plan">
        <h3>Pro Anual</h3>
        <p>R$ 299,00/ano</p>
        <button onclick="checkout('price_anual_id')">Assinar</button>
    </div>
</div>

<script>
async function checkout(priceId) {
    const response = await fetch('/payment/stripe/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            price_id: priceId,
            success_url: window.location.origin + '/success/',
            cancel_url: window.location.origin + '/cancel/'
        })
    });
    
    const data = await response.json();
    window.location.href = data.checkout_url; // Redireciona para Stripe
}
</script>
```

## Segurança

✅ **CodeQL**: Nenhum alerta de segurança encontrado
- Validação de entrada em todas as views
- Uso de `@login_required` para endpoints protegidos
- Tratamento de exceções com logging
- Webhooks validados automaticamente pelo dj-stripe

## Logs e Monitoramento

Todos os eventos são logados:
```python
logger.info(f"Usuário {user.username} atualizado para VIP até {user.vip_expiration}")
logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
```

Configure o logging no `settings.py` para monitorar:
- Pagamentos bem-sucedidos
- Cancelamentos
- Erros de webhook

## Próximos Passos Recomendados

1. **Criar página de gerenciamento de assinatura**
   - Permitir usuário ver plano atual
   - Cancelar assinatura
   - Alterar plano

2. **Adicionar página de histórico de pagamentos**
   - Listar todas as faturas
   - Download de recibos

3. **Implementar período de teste gratuito**
   - Configurar trial period no Stripe

4. **Notificações por email**
   - Confirmação de assinatura
   - Aviso de renovação
   - Falha de pagamento

## Resumo das Mudanças

### Arquivos Criados
- `payment/signals.py` - Handlers de webhook do Stripe
- `payment/services/stripe_service.py` - Funções de sincronização
- `payment/views/views_stripe.py` - Endpoints da API Stripe
- `payment/test_stripe.py` - Testes automatizados

### Arquivos Modificados
- `requirements.txt` - Adicionado dj-stripe==2.10.3
- `server/settings.py` - Configurações do Stripe
- `payment/apps.py` - Import dos signals
- `payment/urls.py` - Rotas do Stripe

### Migrações
- Tabelas do dj-stripe criadas automaticamente (Customer, Subscription, etc.)

---

**Documentação criada em:** 01/11/2025
**Versão dj-stripe:** 2.10.3
**Django:** 5.2.7
