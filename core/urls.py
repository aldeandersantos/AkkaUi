from django.urls import path
from .views import *

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path('api/copy_svg/', copy_svg, name='copy_svg'),
    path('api/paste_svg/', paste_svg, name='paste_svg'),
]