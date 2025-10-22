from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuario/', include('usuario.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG or os.environ.get('SERVE_MEDIA', 'true').lower() in ('1', 'true', 'yes'):
    # Serve media files during development. In production use a proper storage
    # (S3, CDN, etc.). You can disable this behavior by setting
    # SERVE_MEDIA=0 in the environment.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
