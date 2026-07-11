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

# Affichage SQL en console si demandé.
if config("DJANGO_LOG_SQL", default=False, cast=bool):
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# Base de données SQLite pour le développement
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}