from django.urls import path
from .views.views_usuario import *
from .views.views_vip import *
from .views.views_favorites import favoritos, toggle_favorite, get_favorites

app_name = "usuario"

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("signin/", signin, name="signin"),
    path("signout/", signout, name="signout"),
    path("profile/", profile, name="profile"),
    # VIP status endpoint
    path("vip/status/", vip_status, name="vip_status"),
    path("vip/status_all/", vip_status_all, name="vip_status_all"),
    path("vip/add/", vip_status_add, name="vip_status_add"),
    
    path('assinatura/', stripe_customer_portal, name='stripe_customer_portal'),


    # Pegar token
    path("api/token/", get_token, name="api_token"),
    
    # Favoritos
    path("favoritos/", favoritos, name="favoritos"),
    path("api/favorites/toggle/", toggle_favorite, name="toggle_favorite"),
    path("api/favorites/", get_favorites, name="get_favorites"),
]
