# ==========================================
# KPI LOCAL SETTINGS - FINAL STABLE FIX
# ==========================================

SITE_NAME = "ShopnoltdToolbox KPI"
SITE_TITLE = "ShopnoltdToolbox Data Platform"

ALLOWED_HOSTS = ["*"]

# ==========================================
# DATABASE FIX (MERGE SAFE FOR KOBO IMAGE)
# ==========================================

DATABASES = {}

DATABASES["default"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "kpi",
    "USER": "kobo",
    "PASSWORD": "change_me",
    "HOST": "kobo-postgres.kobo.svc.cluster.local",
    "PORT": "5432",
}

DATABASES["kobocat"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "kobocat",
    "USER": "kobo",
    "PASSWORD": "change_me",
    "HOST": "kobo-postgres.kobo.svc.cluster.local",
    "PORT": "5432",
}

DATABASE_ROUTERS = [
    "kobo.apps.kobo_auth.router.KoboRouter",
]

# ==========================================
# PROXY / CLOUDFLARE
# ==========================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = False

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"

# ==========================================
# STATIC / MEDIA
# ==========================================

STATIC_URL = "/static/"
STATIC_ROOT = "/srv/src/kpi/staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/srv/src/kpi/media"

# ==========================================
# CSRF
# ==========================================

CSRF_TRUSTED_ORIGINS = [
    "https://kpi.shopnoltd.dpdns.org",
    "https://shopnoltd.dpdns.org",
]

# ==========================================
# BRANDING
# ==========================================

LOGIN_LOGO = "/static/custom/shopnoltdlogo.png"
FAVICON_URL = "/static/custom/favicon.png"

BRANDING_HEADER = "ShopnoltdToolbox Analytics"
BRANDING_FOOTER = "Powered by Shopnoltd Infrastructure"
