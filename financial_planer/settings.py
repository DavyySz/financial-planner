"""
Django settings for financial_planer project.

Lokal laeuft die App ohne weitere Einrichtung mit SQLite (Datei local.sqlite3).
Ueber Umgebungsvariablen laesst sich alles fuer ein Deployment umstellen:

  DATABASE_URL          z.B. postgres://user:passwort@127.0.0.1:5432/financial_planer
  DJANGO_SECRET_KEY     geheimer Schluessel; fehlt er, wird einer erzeugt und in
  DJANGO_SECRET_KEY_FILE (Standard .secret_key) abgelegt
  DJANGO_DEBUG          "1" (Standard, Entwicklung) oder "0" (Produktion)
  DJANGO_ALLOWED_HOSTS  kommagetrennte Hostnamen/IPs; leer = alle erlauben
  DJANGO_HTTPS          "1", wenn die App hinter HTTPS laeuft (sichere Cookies, Redirect)

Auf einem Server liegen diese Werte in der Datei .env (wird von start.sh gelesen).
"""
import os
import secrets
from pathlib import Path

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Reihenfolge: DJANGO_SECRET_KEY aus der Umgebung/.env; sonst die Datei
# DJANGO_SECRET_KEY_FILE (Standard: .secret_key im Projektordner), die beim
# ersten Start automatisch mit einem zufaelligen Schluessel angelegt wird.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    _key_file = Path(os.environ.get("DJANGO_SECRET_KEY_FILE", BASE_DIR / ".secret_key"))
    try:
        SECRET_KEY = _key_file.read_text().strip()
    except OSError:
        SECRET_KEY = ""
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_urlsafe(50)
        try:
            _key_file.parent.mkdir(parents=True, exist_ok=True)
            _key_file.write_text(SECRET_KEY)
            _key_file.chmod(0o600)
        except OSError:
            pass  # z.B. schreibgeschuetzt: Schluessel gilt dann nur fuer diesen Prozess

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# Welche Hostnamen/IPs die App bedienen darf. Ohne Angabe: alle (damit sie auf
# einem beliebigen Server sofort per IP oder Domain erreichbar ist).
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
if DEBUG or not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://financial-planer-2.fly.dev"]
CSRF_TRUSTED_ORIGINS += [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Hinter einem Reverse-Proxy (Caddy, nginx, fly.io) kommt HTTPS als Header an.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Nur setzen, wenn die App wirklich ueber HTTPS erreichbar ist (DJANGO_HTTPS=1).
if os.environ.get("DJANGO_HTTPS") == "1":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'members',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'members.middleware.LastSeenMiddleware',
]

ROOT_URLCONF = 'financial_planer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'members.context_processors.admin_notices',
            ],
        },
    },
]

WSGI_APPLICATION = 'financial_planer.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
#
# Standard: SQLite-Datei im Projektordner (keine Einrichtung noetig).
# Mit DATABASE_URL (z.B. auf fly.io oder fuer lokales Postgres) wird diese benutzt.
# Die alte Datei db.sqlite3 stammt aus einer frueheren Projektversion und ist nicht kompatibel.

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'local.sqlite3'}",
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"
