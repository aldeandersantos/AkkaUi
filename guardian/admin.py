from django.contrib import admin
from .models import FileAsset


@admin.register(FileAsset)
class FileAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_path', 'owner', 'uploaded_at')
    list_filter = ('uploaded_at', 'owner')
    search_fields = ('name', 'file_path', 'owner__username')
    readonly_fields = ('uploaded_at',)
