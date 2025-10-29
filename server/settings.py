
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / 'env/.env'
# Use python-dotenv to load environment variables from .env without
# overriding existing environment variables (preserves current behavior).
if env_path.exists():
    # load_dotenv accepts a path-like or string path; override=False
    # ensures we do not overwrite already-set environment variables.
    load_dotenv(dotenv_path=str(env_path), override=False)

# Read DEBUG first so we can decide how strict to be when SECRET_KEY is missing.
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')

# production (DEBUG=False) we require SECRET_KEY to be set.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        # Development fallback (not for production)
        SECRET_KEY = 'dev-secret-change-me'
    else:
        raise RuntimeError("SECRET_KEY not found in environment; set it in .env for production")

raw_allowed = os.getenv('ALLOWED_HOSTS', '').strip()
if raw_allowed:
    try:
        import json

        parsed = json.loads(raw_allowed)
        if isinstance(parsed, (list, tuple)):
            ALLOWED_HOSTS = [str(h).strip() for h in parsed if str(h).strip()]
        else:
            # If JSON parsed to a single value, fall back to comma-split
            ALLOWED_HOSTS = [p.strip() for p in str(parsed).split(',') if p.strip()]
    except Exception:
        # Not JSON: parse as comma-separated string
        ALLOWED_HOSTS = [h.strip() for h in raw_allowed.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = []

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'payment',
    'usuario',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Project-level templates directory. We'll place app templates under
        # BASE_DIR / 'templates' / '<app_name>' (e.g. templates/core/)
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('pt-br', 'Português (Brasil)'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('zh-hans', '中文 (简体)'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = 'static/'

# During development, collect static files from the project-level `static/`
# directory. We'll organize static files by app under `static/<app_name>/`.
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Directory where `collectstatic` will collect static files for production.
# You can change this when deploying.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads)
# Durante desenvolvimento usamos MEDIA_URL e MEDIA_ROOT para servir imagens
# enviadas pelos usuários (thumbnails). Em produção configure um storage
# externo e não sirva media diretamente pelo Django.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'usuario.CustomUser'

# Login/Logout URLs
LOGIN_URL = '/usuario/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Upload limits
# Aumenta o limite para aceitar SVGs maiores via JSON (request.body).
# Valores podem ser ajustados via variáveis de ambiente.
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MEMORY_SIZE', str(50 * 1024 * 1024)))  # 50 MB
# Para uploads multipart/form-data, controla quando arquivos vão para memória vs. disco temporário
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MEMORY_SIZE', str(50 * 1024 * 1024)))  # 50 MB



# Environment-specific API keys
ABACATE_API_TEST_KEY = os.getenv('ABACATE_API_TEST_KEY')
ABACATE_API_PROD_KEY = os.getenv('ABACATE_API_PROD_KEY')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN')


# Discord Webhook URLs
DISCORD_WEBHOOK_GEROU_COMPRA = os.getenv('WEBHOOK_DISCORD_GEROU_COMPRA')
DISCORD_WEBHOOK_CONFIRMOU_PAGAMENTO = os.getenv('WEBHOOK_DISCORD_CONFIRMOU_PAGAMENTO')
DISCORD_WEBHOOK_ENTROU_PRECO = os.getenv('WEBHOOK_DISCORD_ENTROU_PRECO')
DISCORD_WEBHOOK_CRIOU_CONTA = os.getenv('WEBHOOK_DISCORD_CRIOU_CONTA')
DISCORD_WEBHOOK_ADQUIRIU_ASSINATURA = os.getenv('WEBHOOK_DISCORD_ADQUIRIU_ASSINATURA')
