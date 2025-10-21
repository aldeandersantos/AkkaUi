from django.contrib import admin
from .models import UiWikiComponent, SvgAsset

# Register your models here.


@admin.register(UiWikiComponent)
class UiWikiComponentAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'autor', 'data_importacao')
    list_filter = ('categoria', 'data_importacao')
    search_fields = ('nome', 'autor', 'tags')


@admin.register(SvgAsset)
class SvgAssetAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_criacao', 'data_atualizacao')
    list_filter = ('data_criacao', 'data_atualizacao')
    search_fields = ('nome', 'descricao', 'tags')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'tags')
        }),
        ('Conteúdo SVG', {
            'fields': ('svg_text', 'svg_file')
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
