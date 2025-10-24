from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""
    # Mostrar uma versão curta do hash na listagem para melhor leitura
    list_display = [
        'username', 'email', 'phone', 'admin', 'is_staff', 'is_active',
        'is_vip', 'vip_expiration', 'hash_preview', 'date_joined'
    ]
    list_filter = ['admin', 'is_staff', 'is_superuser', 'is_active', 'is_vip', 'vip_expiration', 'date_joined']
    search_fields = ['username', 'email', 'phone']
    # Allow quick edit of VIP status from the list view. Keep username as the link.
    list_editable = ['is_vip']
    list_display_links = ('username',)

    # Campos somente leitura que aparecem no form de alteração
    readonly_fields = ('hash_readable',)

    # Inclui o campo hash no form de alteração (somente leitura)
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('phone', 'admin', 'is_vip', 'vip_expiration')}),
        ('Identificador', {'fields': ('hash_readable',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Adicionais', {'fields': ('email', 'phone', 'admin', 'is_vip', 'vip_expiration')}),
    )

    def hash_preview(self, obj):
        """Mostra versão curta do hash na list_display."""
        if not obj.hash_id:
            return '-'
        # mostra os primeiros 8 e últimos 6 caracteres para legibilidade
        return f"{obj.hash_id[:8]}...{obj.hash_id[-6:]}"
    hash_preview.short_description = 'Hash'

    def hash_readable(self, obj):
        """Mostra o hash completo no detail view com formatação fixa."""
        if not obj.hash_id:
            return '-'
        # Usa <code> para facilitar a cópia visual
        return format_html('<code style="word-break:break-all;">{}</code>', obj.hash_id)
    hash_readable.short_description = 'Hash ID'
