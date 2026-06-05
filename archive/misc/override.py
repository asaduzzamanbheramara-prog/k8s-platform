from .base import *
import os

DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY", "shopnoltd-production-secret")

ALLOWED_HOSTS = ["*"]

# ============================
# CRITICAL FIX: 2 DATABASES
# ============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "kpi",
        "USER": "kobo",
        "PASSWORD": "change_me",
        "HOST": "kobo-postgres.kobo.svc.cluster.local",
        "PORT": "5432",
    },
    "kobocat": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "kobocat",
        "USER": "kobo",
        "PASSWORD": "change_me",
        "HOST": "kobo-postgres.kobo.svc.cluster.local",
        "PORT": "5432",
    },
}

KOBOCAT_URL = "https://kf.shopnoltd.dpdns.org"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = False

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "https://kpi.shopnoltd.dpdns.org",
    "https://kf.shopnoltd.dpdns.org",
    "https://kobo.shopnoltd.dpdns.org",
    "https://shopnoltd.dpdns.org",
]

STATIC_URL = "/static/"
STATIC_ROOT = "/srv/src/kpi/staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/srv/src/kpi/media"

SITE_NAME = "ShopnoltdToolbox KPI"
SITE_TITLE = "ShopnoltdToolbox Data Platform"

LOGIN_LOGO = "/static/custom/shopnoltdlogo.png"
FAVICON_URL = "/static/custom/favicon.png"

X_FRAME_OPTIONS = "SAMEORIGIN"
