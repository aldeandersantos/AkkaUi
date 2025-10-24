from django.urls import path
from .views.views_usuario import *
from .views.views_vip import *

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

    # Pegar token
    path("api/token/", get_token, name="api_token"),
]
