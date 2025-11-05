from django.contrib import admin
from .models import Payment, PaymentItem, Purchase


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


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'svg', 'price', 'payment_method', 'purchased_at')
    list_filter = ('payment_method', 'purchased_at')
    search_fields = ('user__username', 'user__email', 'svg__title_name')
    readonly_fields = ('purchased_at',)
    ordering = ('-purchased_at',)
    
    fieldsets = (
        ('Informações da Compra', {
            'fields': ('user', 'svg', 'price', 'payment_method')
        }),
        ('Timestamp', {
            'fields': ('purchased_at',)
        }),
    )


# --- Segurança para admin do dj-stripe Customer ---
# Tentativa não intrusiva de substituir o CustomerAdmin do dj-stripe
# por uma versão resiliente que evita avaliar properties que podem
# executar consultas inválidas durante a construção dos readonly fields.
try:
    from djstripe import models as djstripe_models
    from djstripe.admin.admin import CustomerAdmin as DjstripeCustomerAdmin

    try:
        admin.site.unregister(djstripe_models.Customer)
    except Exception:
        # pode já ter sido desregistrado ou não registrado
        pass


    class SafeCustomerAdmin(DjstripeCustomerAdmin):
        def get_readonly_fields(self, request, obj=None):
            """Get readonly fields but remove any that raise when accessed on obj.

            We attempt to call getattr(obj, name) for each candidate readonly
            field and drop the ones that raise an exception (FieldError or
            others). This prevents the admin template from failing when it
            renders readonly properties that perform unsafe ORM lookups.
            """
            try:
                fields = list(super().get_readonly_fields(request, obj=obj))
            except Exception:
                return ("livemode", "id", "djstripe_owner_account", "created")

            if obj is None:
                # no instance to test against; return fields as-is but still
                # filter obvious problematic names
                blacklist = {"active_subscriptions", "current_period_end", "current_period_start"}
                return [f for f in fields if f not in blacklist]

            safe_fields = []
            for name in fields:
                try:
                    # attempt to access the attribute on the instance; some
                    # properties perform queryset operations and will raise
                    # FieldError or other exceptions — catch and skip them.
                    _ = getattr(obj, name)
                except Exception:
                    # skip problematic readonly field
                    continue
                else:
                    safe_fields.append(name)

            return safe_fields


    admin.site.register(djstripe_models.Customer, SafeCustomerAdmin)
except Exception:
    # djstripe não está instalado ou ocorreu erro importando - ignorar silenciosamente
    pass
