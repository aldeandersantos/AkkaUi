from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/reply/', views.ticket_reply, name='ticket_reply'),
    path('tickets/<int:ticket_id>/status/', views.ticket_update_status, name='ticket_update_status'),
    path('tickets/<int:ticket_id>/toggle-uploads/', views.ticket_toggle_client_uploads, name='ticket_toggle_uploads'),
]
