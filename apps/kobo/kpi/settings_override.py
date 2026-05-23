import os

# Try safe import from base kpi settings
try:
    from kpi.settings import *
except Exception:
    pass

# =========================
# DATABASES (REQUIRED FIX)
# =========================

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

# =========================
# CELERY FIX
# =========================

CELERY_BROKER_URL = "redis://redis.kobo.svc.cluster.local:6379/1"

# =========================
# REDIS
# =========================

REDIS_URL = "redis://redis.kobo.svc.cluster.local:6379/0"

# =========================
# MONGO
# =========================

MONGO_DB_URL = "mongodb://mongo.kobo.svc.cluster.local:27017/kobo"

# =========================
# HOSTS
# =========================

ALLOWED_HOSTS = ["*"]

# =========================
# FORCE SAFE MODE
# =========================

KPI_DATABASE_CHECK_OVERRIDE = True
KPI_SKIP_MONGO_COMPATIBILITY_CHECK = True
