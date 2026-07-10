"""Commande : archive les alertes traitées anciennes (BF04).

Usage :
  python manage.py archiver_alertes          # 90 jours par défaut
  python manage.py archiver_alertes --jours 30
"""
from django.core.management.base import BaseCommand

from apps.alerts.services import archiver_anciennes_alertes


class Command(BaseCommand):
    help = "Archive les alertes traitées de plus de N jours"

    def add_arguments(self, parser):
        parser.add_argument(
            "--jours", type=int, default=90,
            help="Âge minimum (en jours) des alertes à archiver (défaut : 90)",
        )

    def handle(self, *args, **options):
        jours = options["jours"]
        count = archiver_anciennes_alertes(jours)
        self.stdout.write(self.style.SUCCESS(
            f"[ARCHIVAGE] {count} alerte(s) archivée(s) (> {jours} jours)."
        ))
