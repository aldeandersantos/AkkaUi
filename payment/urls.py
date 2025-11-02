from django.urls import path, include
from payment.views import *
from payment.views.views_payment import *
from payment.views.views_webhook import abacatepay_webhook, mercadopago_webhook
from payment.views.views_purchases import purchased_svgs_page, purchased_svgs_api, create_purchase
from payment.views.views_stripe import (
    create_checkout_session,
    list_subscription_prices,
    user_subscription_status,
    stripe_webhook
)

app_name = "payment"

urlpatterns = [
    # APIs genéricas de pagamento
    path("create/", create_payment, name="create_payment"),
    path("check-status/", check_payment_status_view, name="check_payment_status"),
    path("simulate/", simulate_payment_view, name="simulate_payment"),
    path("list/", list_user_payments, name="list_user_payments"),
    
    # Webhook do AbacatePay para confirmação automática
    path("webhook/abacatepay/", abacatepay_webhook, name="abacatepay_webhook"),
    path("webhook/mercadopago/", mercadopago_webhook, name="mercadopago_webhook"),
    
    # APIs legadas do Abacate Pay (mantidas para compatibilidade)
    path("abacate-status/", abacate_status, name="abacate_status"),
    path("simulate-sale/", simulate_sale, name="simulate_sale"),
    path("simulate-confirmation/", simulate_confirmation, name="simulate_confirmation"),
    
    # SVGs comprados
    path("meus-svgs/", purchased_svgs_page, name="purchased_svgs"),
    path("api/users/<int:user_id>/purchased-svgs/", purchased_svgs_api, name="purchased_svgs_api"),
    path("api/purchase/create/", create_purchase, name="create_purchase"),
    
    # Stripe - Assinaturas
    path("stripe/checkout/", create_checkout_session, name="stripe_checkout"),
    path("stripe/prices/", list_subscription_prices, name="stripe_prices"),
    path("stripe/subscription-status/", user_subscription_status, name="stripe_subscription_status"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    
    # URLs do dj-stripe (webhooks e admin)
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
]