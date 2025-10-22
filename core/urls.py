from django.urls import path
from .views import *

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("explore/", explore, name="explore"),
    path("pricing/", pricing, name="pricing"),
    path("faq/", faq, name="faq"),
    path('api/copy_svg/', copy_svg, name='copy_svg'),
    path('api/paste_svg/', paste_svg, name='paste_svg'),
    path('manage/svg/', admin_svg, name='admin_svg'),
    path('manage/svg/create/', admin_create_svg, name='admin_create_svg'),
    path('api/manage/svg/delete/', admin_delete_svg, name='admin_delete_svg'),
]