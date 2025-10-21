from django.contrib import admin
from django.utils.html import format_html

from .models import UiWikiComponent


@admin.register(UiWikiComponent)
class UiWikiComponentAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'categoria', 'autor', 'data_importacao', 'thumbnail_preview')
    search_fields = ('nome', 'categoria', 'autor', 'tags')
    list_filter = ('categoria', 'autor', 'data_importacao')
    readonly_fields = ('data_importacao', 'thumbnail_preview')
    fieldsets = (
        (None, {'fields': ('nome', 'categoria', 'link_figma', 'autor', 'tags', 'thumbnail_url')}),
        ('Metadados', {'fields': ('data_importacao', 'thumbnail_preview')}),
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="max-height:120px; max-width:200px; object-fit:contain;"/>', obj.thumbnail_url)
        return '(sem thumbnail)'

    thumbnail_preview.short_description = 'Thumbnail'