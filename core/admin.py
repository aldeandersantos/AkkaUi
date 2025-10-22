from django.contrib import admin
from django.utils.html import format_html
from .models import SvgFile


@admin.register(SvgFile)
class SvgFileAdmin(admin.ModelAdmin):
	list_display = ("id", "title_name", "uploaded_at")
	search_fields = ("title_name",)
	ordering = ("-uploaded_at",)
