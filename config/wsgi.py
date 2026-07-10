"""Point d'entrée WSGI pour les serveurs de production (Gunicorn/uWSGI)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
