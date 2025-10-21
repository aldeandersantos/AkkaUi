from django.contrib import admin
from django.utils.html import format_html
from .models import SvgFile


@admin.register(SvgFile)
class SvgFileAdmin(admin.ModelAdmin):
	list_display = ("id", "filename", "uploaded_at")
	search_fields = ("filename",)
	ordering = ("-uploaded_at",)
