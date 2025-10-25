from django.urls import path
from payment.views import *

app_name = "payment"

urlpatterns = [
    path("abacate-status/", abacate_status, name="abacate_status"),
    path("simulate-sale/", simulate_sale, name="simulate_sale"),
    path("simulate-confirmation/", simulate_confirmation, name="simulate_confirmation"),
    path("meus-svgs/", purchased_svgs_page, name="purchased_svgs"),
    path("api/users/<int:user_id>/purchased-svgs/", purchased_svgs_api, name="purchased_svgs_api"),
    path("api/purchase/create/", create_purchase, name="create_purchase"),
]