from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'gateway', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('gateway', 'status', 'plan', 'created_at')
    search_fields = ('transaction_id', 'gateway_payment_id', 'user__username', 'user__email')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'completed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': ('user', 'gateway', 'plan', 'amount', 'currency', 'status')
        }),
        ('IDs e Transação', {
            'fields': ('transaction_id', 'gateway_payment_id')
        }),
        ('Metadados', {
            'fields': ('gateway_response', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
