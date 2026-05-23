SITE_NAME = "Shopnoltd KPI"
SITE_TITLE = "Shopnoltd Data Platform"

ALLOWED_HOSTS = ["*"]

# FIX: Django health endpoint MUST NOT use urlpatterns here
# Instead we ensure Django loads properly via middleware/urls in project

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "kpi",
        "USER": "kobo",
        "PASSWORD": "change_me",
        "HOST": "kobo-postgres.kobo.svc.cluster.local",
        "PORT": "5432",
    }
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

CSRF_TRUSTED_ORIGINS = [
    "https://kpi.shopnoltd.dpdns.org"
]

BRANDING_HEADER = "Shopnoltd Analytics"
BRANDING_FOOTER = "Powered by Shopnoltd Cloud"
