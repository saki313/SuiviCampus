"""
Réglages de base du projet Django — Plateforme de Suivi Académique.

Séparation stricte (Clean Architecture) :
  - Aucune logique métier ici (le métier vit dans `domain/` et `apps/*/services/`).
  - Cette configuration ne fait que câbler l'infrastructure Django/DRF.

Les sous-classes dev.py / prod.py héritent et surchargent.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config

# --- Chemins -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Sécurité / clé ----------------------------------------------------------
SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = False  # surchargé à True en dev

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1"
).split(",")

# --- Applications -------------------------------------------------------------
# Ordre volontaire : common d'abord (bases), puis domain-agnostic, puis métier.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Tiers
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",

    # Locales — common
    "apps.common",
    "apps.audit",

    # Locales — comptes & RBAC
    "apps.accounts",

    # Locales — métier académique
    "apps.academics",
    "apps.warehouse",

    # Locales — analytique & risque
    "apps.analytics",
    "apps.risk",
    "apps.alerts",

    # Locales — intégration & restitution
    "apps.etl",
    "apps.reporting",
    "apps.dashboards",
]

# Reverse / templates : on pointe vers presentation/ pour la couche présentation
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Journalisation d'audit (BF sécurité / audit)
    "apps.audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "presentation" / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de données (PostgreSQL / Data Warehouse) ----------------------------
# Surcharge via DATABASE_URL (dj-database-url). Fallback sqlite pour tests isolés.
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL",
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Pagination/filtres par défaut pour les champs texte (PostgreSQL).
if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
    DATABASES["default"]["OPTIONS"] = {"options": "-c timezone=Africa/Ouagadougou"}

# --- Authentification : modèle Utilisateur personnalisée ----------------------
AUTH_USER_MODEL = "accounts.Utilisateur"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"  # Redirige vers /dashboard/ → _redirect_par_role()

# --- Configuration du site Django admin -----------------------------------------------
# Site ID pour Django (utilisé par django.contrib.sites)
SITE_ID = 1

# Les éléments suivants sont utilisés par config/admin_config.py
ADMIN_URL_BASE = "/admin/"
ADMIN_SITE_HEADER = "Suivi Académique — Administration"
ADMIN_SITE_TITLE = "Suivi Académique"
ADMIN_INDEX_TITLE = "Gestion du système"

# --- Internationalisation -----------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Ouagadougou"
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques -------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "presentation" / "static"]

# --- Champ identifiant par défaut --------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ----------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # pour l'admin/browse
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "30/min", "user": "300/min"},
}

# --- JWT (BF12 - contrôle d'accès) -------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_MINUTES", default=60, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- OpenAPI / Swagger --------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "API Suivi Académique",
    "DESCRIPTION": (
        "Plateforme décisionnelle de suivi académique — complémentaire à "
        "service.campusfaso.bf (lecture seule). "
        "Expose les KPI, scores de risque, alertes et parcours étudiants."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- ETL ----------------------------------------------------------------------
ETL_SOURCE_MODE = config("ETL_SOURCE_MODE", default="mock")  # "mock" | "api"
ETL_CAMPUSFASO_BASE_URL = config(
    "ETL_CAMPUSFASO_BASE_URL", default="https://service.campusfaso.bf"
)
ETL_CAMPUSFASO_API_TOKEN = config("ETL_CAMPUSFASO_API_TOKEN", default="")

# --- Journaux -----------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} :: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "domain": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# --- Protection par défaut ---------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = False  # True en prod
CSRF_COOKIE_SECURE = False     # True en prod
