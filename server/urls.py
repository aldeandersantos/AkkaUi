from django.contrib import admin
from django.urls import path, re_path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.views.static import serve
from django.http import Http404
import os

# Custom view to serve only non-protected media files in development
def serve_public_media(request, path):
    """
    Serve media files in development, but block access to private directory.
    In production, Nginx should handle all /media/ requests and return 403.
    """
    # Block access to private files even in development
    if path.startswith('private/'):
        raise Http404("File not found")
    
    # Serve non-private media files
    return serve(request, path, document_root=settings.MEDIA_ROOT)

# Rotas que NÃO DEVEM TER PREFIXO DE IDIOMA
urlpatterns = [
    path('stripe/', include('djstripe.urls', namespace='djstripe')),
    path('i18n/setlang/', set_language, name='set_language'),
    path('admin/', admin.site.urls),
    path('payment/', include('payment.urls')),
]

# Rotas que DEVEM TER PREFIXO DE IDIOMA
urlpatterns += i18n_patterns(
    path('usuario/', include('usuario.urls')),
    path('support/', include('support.urls')),
    path('guardian/', include('guardian.urls')),
    path('', include('core.urls')),
    prefix_default_language=True,
)

# Serve media files during development with protection for private files
if settings.DEBUG:
    # Use custom view that blocks private/ directory
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_public_media),
    ]
elif os.environ.get('SERVE_MEDIA', 'false').lower() in ('1', 'true', 'yes'):
    # Allow serving all media only when explicitly enabled (not recommended)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files during development or when explicitly enabled
if settings.DEBUG:
    # Always serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif os.environ.get('SERVE_STATIC', 'false').lower() in ('1', 'true', 'yes'):
    # In production with DEBUG=False, serve static files via Django
    # This uses Django's staticfiles app to serve from both STATIC_ROOT and STATICFILES_DIRS
    from django.contrib.staticfiles.views import serve as staticfiles_serve
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', staticfiles_serve),
    ]
