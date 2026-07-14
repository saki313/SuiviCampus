"""Réglages de DÉVELOPPEMENT (DEBUG, formats lisibles, relaxations de sécurité)."""
from .base import *  # noqa: F401,F403
from decouple import config

DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

# En dev, on tolère localhost et l'hôte de la VM/conteneur.
ALLOWED_HOSTS = ["*"]

# CORS permissif en développement local (interopérabilité front séparé éventuel).
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Mots de passe non hachés en clair => vitesse (NE PAS FAIRE EN PROD).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Email en console pour les notifications d'alerte (BF04).
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "suivi-academique@localhost"

# Base de données SQLite pour le développement
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Backend d'authentification avec traces
AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.TraceBackend',
]

# Logs pour tracer l'authentification
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} :: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'auth_trace.log',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.contrib.auth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'apps.dashboards.views_auth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Affichage SQL en console si demandé.
if config("DJANGO_LOG_SQL", default=False, cast=bool):
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }