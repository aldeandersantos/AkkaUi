from server.settings import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_extensions']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

DEBUG = True
PROD = False
SECRET_KEY = 'test-secret-key-for-testing-only'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

MEDIA_ROOT = BASE_DIR / 'test_media'
STATIC_ROOT = BASE_DIR / 'test_static'
