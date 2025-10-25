from django.contrib import admin
from .models import Payment, PaymentItem


class PaymentItemInline(admin.TabularInline):
    model = PaymentItem
    extra = 0
    readonly_fields = ('total_price', 'created_at')
    fields = ('item_type', 'item_name', 'quantity', 'unit_price', 'total_price')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'gateway', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('gateway', 'status', 'plan', 'created_at')
    search_fields = ('transaction_id', 'gateway_payment_id', 'user__username', 'user__email')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'completed_at')
    ordering = ('-created_at',)
    inlines = [PaymentItemInline]
    
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


@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = ('payment', 'item_type', 'item_name', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('item_type', 'created_at')
    search_fields = ('item_name', 'payment__transaction_id')
    readonly_fields = ('total_price', 'created_at')
    ordering = ('-created_at',)
