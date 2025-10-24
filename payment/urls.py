from django.urls import path
from payment.views.views_abacate import *

app_name = "payment"

urlpatterns = [
    path("abacate-status/", abacate_status, name="abacate_status"),
    path("simulate-sale/", simulate_sale, name="simulate_sale"),
    path("simulate-confirmation/", simulate_confirmation, name="simulate_confirmation"),
]