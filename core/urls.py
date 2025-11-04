from django.urls import path
from .views import *
# Importar views de pagamento para rotas públicas de sucesso/cancel
from payment.views.views_stripe import SuccessView, CancelView

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("explore/", explore, name="explore"),
    path("pricing/", pricing, name="pricing"),
    path("faq/", faq, name="faq"),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('minha-biblioteca/', minha_biblioteca, name='minha_biblioteca'),
    path('api/copy_svg/', copy_svg, name='copy_svg'),
    path('api/paste_svg/', paste_svg, name='paste_svg'),
    path('api/search_svg/', search_svg, name='search_svg'),
    path('manage/svg/', admin_svg, name='admin_svg'),
    path('manage/svg/create/', admin_create_svg, name='admin_create_svg'),
    path('api/manage/svg/delete/', admin_delete_svg, name='admin_delete_svg'),
    # Páginas públicas de sucesso/cancel após checkout (Stripe)
    path('success/', SuccessView.as_view(), name='payment_success'),
    path('cancel/', CancelView.as_view(), name='payment_cancel'),
]