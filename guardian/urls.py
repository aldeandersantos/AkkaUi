from django.urls import path
from . import views

app_name = 'guardian'

urlpatterns = [
    path('download/<int:file_id>/', views.protected_media, name='protected_media'),
]
