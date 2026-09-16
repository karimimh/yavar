"""
Production settings.

This is a placeholder skeleton: values are intentionally strict and must be
provided via environment variables. Harden further before a real deployment.
"""

from config.settings.base import *  # noqa: F403
from config.settings.base import env

DEBUG = False

# Required in production; no insecure default.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
