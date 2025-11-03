"""
Entrypoint WSGI para deploy do AkkaUi.

Este arquivo expõe a variável WSGI `application` e garante que a raiz
do projeto esteja em `sys.path`. Ele usa o mesmo módulo de settings
definido em `manage.py` e `server/wsgi.py` (server.settings).
"""
import os
import sys

# garantir que a raiz do projeto esteja no sys.path
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
