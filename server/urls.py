from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
import os

urlpatterns = [
    path('i18n/setlang/', set_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('usuario/', include('usuario.urls')),
    path('payment/', include('payment.urls')),
    path('support/', include('support.urls')),
    path('', include('core.urls')),
    prefix_default_language=True,
)

if settings.DEBUG or os.environ.get('SERVE_MEDIA', 'true').lower() in ('1', 'true', 'yes'):
    # Serve media files during development. In production use a proper storage
    # (S3, CDN, etc.). You can disable this behavior by setting
    # SERVE_MEDIA=0 in the environment.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
