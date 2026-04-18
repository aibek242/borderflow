import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "borderflow.duckdns.org",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://borderflow.duckdns.org",
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",  # Для работы с Supabase S3
    "shipments.apps.ShipmentsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # Для статики на Render
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "shipments" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"

# ================= DATABASE (Настройки Supabase Postgres) =================
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Qyzylorda"
USE_I18N = True
USE_TZ = True

# ================= STATIC FILES (Настройки WhiteNoise) =================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# ================= MEDIA & STORAGE =================
USE_S3 = os.getenv("USE_S3", "False") == "True"
# Мы временно ПРИНУДИТЕЛЬНО ставим True, чтобы проверить,
# изменятся ли ссылки в логах Render при запуске
print(f"DEBUG: USE_S3 is set to {USE_S3}") # Это отобразится в логах Render при запуске

if USE_S3:
    AWS_ACCESS_KEY_ID = os.getenv("SUPABASE_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("SUPABASE_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("SUPABASE_ENDPOINT")
    AWS_S3_REGION_NAME = "us-east-1"
    AWS_QUERYSTRING_AUTH = False  # Отключаем подписи в ссылках
    AWS_S3_FILE_OVERWRITE = False

    # 1. Вырезаем ID проекта (например, 'avtyw...') из эндпоинта
    PROJECT_ID = AWS_S3_ENDPOINT_URL.split('//')[1].split('.')[0]

    # 2. Указываем кастомный домен для публичных ссылок
    AWS_S3_CUSTOM_DOMAIN = f"{PROJECT_ID}.supabase.co/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}"

    # 3. Финальный MEDIA_URL будет выглядеть как прямая ссылка
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ================= AUTH & SECURITY =================
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/home/"
LOGOUT_REDIRECT_URL = "/login/"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG