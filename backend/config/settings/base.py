"""
Base Django settings shared by all environments.

Environment-specific settings live in development.py and production.py.
Configuration values are read from environment variables (optionally via a
.env file at the repository root) using django-environ.
"""

from pathlib import Path

import environ

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# Read a .env file from the repository root if present (local development
# outside Docker). In Docker, variables are injected by docker-compose.
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-development-only-key")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.billing",
    "apps.conversations",
    "apps.tasks",
    "apps.approvals",
    "apps.reminders",
    "apps.notifications",
    "apps.memory",
    "apps.coverage",
    "apps.research",
    "apps.travel",
    "apps.bills",
    "apps.requests",
    "apps.agent",
    "apps.operators",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="yavar"),
        "USER": env("POSTGRES_USER", default="yavar"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="yavar"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        # 5433 matches the host port published by docker-compose for Postgres.
        "PORT": env("POSTGRES_PORT", default="5433"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Sessions: HTTP-only cookie, no tokens in localStorage.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "tick-due-reminders": {
        "task": "apps.agent.tasks.tick_due_reminders",
        "schedule": 15.0,
    },
    "purge-screenshots": {
        "task": "apps.agent.tasks.purge_expired_screenshots",
        "schedule": 3600.0,
    },
    "purge-temp-ids": {
        "task": "apps.agent.tasks.purge_temporary_identifiers",
        "schedule": 3600.0,
    },
}

# Integrations — sandbox by default; missing keys never fabricate facts.
LLM_BASE_URL = env("LLM_BASE_URL", default="https://api.openai.com/v1")
LLM_API_KEY = env("LLM_API_KEY", default="")
LLM_MODEL = env("LLM_MODEL", default="gpt-4o-mini")
SMS_PROVIDER = env("SMS_PROVIDER", default="console")
PROVIDER_MODE = env("PROVIDER_MODE", default="sandbox")
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="sandbox")
