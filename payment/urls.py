from django.urls import path
from payment.views import *
from payment.views.views_payment import *
from payment.views.views_webhook import abacatepay_webhook, mercadopago_webhook
from payment.views.views_purchases import purchased_svgs_page, purchased_svgs_api, create_purchase

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
]