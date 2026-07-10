"""Commande de gestion : exécute un cycle ETL complet.

Usage :
  python manage.py etl_run                  # synchronisation différentielle
  python manage.py etl_run --full           # synchronisation complète (force)
  python manage.py etl_run --no-kpi         # sans recalcul KPI/alertes ensuite
"""
from django.core.management.base import BaseCommand

from apps.etl.services.pipeline import executer_etl


class Command(BaseCommand):
    help = "Exécute un cycle ETL : extraction campusfaso.bf → transformation → chargement DW"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full", action="store_true",
            help="Synchronisation complète (ignore les checkpoints différentiels)",
        )
        parser.add_argument(
            "--no-kpi", action="store_true",
            help="Ne pas déclencher le recalcul KPI / alertes après l'ETL",
        )

    def handle(self, *args, **options):
        differentiel = not options["full"]
        self.stdout.write(self.style.WARNING(
            f"[ETL] Démarrage (différentiel={differentiel})..."
        ))
        run = executer_etl(differentiel=differentiel)

        self.stdout.write(self.style.SUCCESS(
            f"[ETL] Run #{run.id} terminé : {run.statut}\n"
            f"  Étudiants : {run.nb_etudiants_charges}\n"
            f"  UE        : {run.nb_ue_charges}\n"
            f"  Résultats : {run.nb_resultats_charges}\n"
            f"  Présences : {run.nb_presences_extraites}\n"
            f"  Erreurs   : {run.nb_erreurs}"
        ))

        # Recalcul KPI + alertes (DS1, DS2) après l'ETL — sauf si --no-kpi
        if not options["no_kpi"] and run.statut == run.Statut.SUCCES:
            self.stdout.write(self.style.WARNING("[KPI] Recalcul des indicateurs..."))
            from apps.analytics.services import calculer_indicateurs_promotion
            nb = calculer_indicateurs_promotion()
            self.stdout.write(self.style.SUCCESS(f"[KPI] {nb} étudiants recalculés."))

            self.stdout.write(self.style.WARNING("[ALERTES] Vérification des seuils..."))
            from apps.alerts.services import verifier_promotion
            nb_alertes = verifier_promotion()
            self.stdout.write(self.style.SUCCESS(
                f"[ALERTES] {nb_alertes} alerte(s) générée(s)."
            ))
