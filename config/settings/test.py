"""Réglages de TEST — utilise SQLite pour isolation et rapidité (Phase 13).

Charge en priorité la base SQLite pour exécuter les tests sans dépendre
d'un serveur PostgreSQL disponible. L'architecture n'est pas modifiée :
seul l'adaptateur de base de données change pour les tests.

Usage :
    DJANGO_SETTINGS_MODULE=config.settings.test pytest
"""
from .dev import *  # noqa: F401,F403

# Base de données de test : SQLite en mémoire (rapide, isolé, sans serveur)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Les migrations de mots de passe MD5 en dev restent OK pour les tests
# (accélère la création d'utilisateurs de test)
