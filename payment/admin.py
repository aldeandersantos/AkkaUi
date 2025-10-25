from django.contrib import admin
from .models import Purchase


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'svg', 'purchased_at', 'price', 'payment_method']
    list_filter = ['purchased_at', 'payment_method']
    search_fields = ['user__username', 'svg__title_name']
    date_hierarchy = 'purchased_at'
    readonly_fields = ['purchased_at']
