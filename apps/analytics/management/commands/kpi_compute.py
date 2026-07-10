"""Commande : recalcule les indicateurs KPI + alertes (BF02, BF04, BF06).

Usage :
  python manage.py kpi_compute              # recalcul global + alertes
  python manage.py kpi_compute --etudiant MAT0001  # un seul étudiant
  python manage.py kpi_compute --no-alertes # sans générer d'alertes
"""
from django.core.management.base import BaseCommand

from apps.analytics.services import (
    calculer_indicateurs_etudiant, calculer_indicateurs_promotion,
)
from apps.alerts.services import verifier_et_generer_alertes, verifier_promotion
from apps.accounts.models import ProfilEtudiant


class Command(BaseCommand):
    help = "Recalcule les scores de risque et indicateurs KPI, puis génère les alertes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--etudiant", type=str, default="",
            help="Matricule d'un étudiant spécifique (sinon : toute la promotion)",
        )
        parser.add_argument(
            "--no-alertes", action="store_true",
            help="Ne pas générer les alertes après le recalcul",
        )

    def handle(self, *args, **options):
        matricule = options["etudiant"]
        generer_alertes = not options["no_alertes"]

        if matricule:
            try:
                etudiant = ProfilEtudiant.objects.get(matricule=matricule)
            except ProfilEtudiant.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f"Étudiant {matricule} introuvable."
                ))
                return
            self.stdout.write(self.style.WARNING(
                f"[KPI] Recalcul pour {matricule}..."
            ))
            indic = calculer_indicateurs_etudiant(etudiant)
            self.stdout.write(self.style.SUCCESS(
                f"[KPI] Score={indic.score_risque:.1f} ({indic.classification_risque}), "
                f"progression={indicateur_libelle(indic)}"
            ))
            if generer_alertes:
                nb = len(verifier_et_generer_alertes(etudiant))
                self.stdout.write(self.style.SUCCESS(
                    f"[ALERTES] {nb} alerte(s) pour {matricule}."
                ))
        else:
            self.stdout.write(self.style.WARNING(
                "[KPI] Recalcul global des indicateurs..."
            ))
            count = calculer_indicateurs_promotion()
            self.stdout.write(self.style.SUCCESS(f"[KPI] {count} étudiants recalculés."))
            if generer_alertes:
                self.stdout.write(self.style.WARNING(
                    "[ALERTES] Vérification des seuils..."
                ))
                nb = verifier_promotion()
                self.stdout.write(self.style.SUCCESS(
                    f"[ALERTES] {nb} alerte(s) générée(s)."
                ))


def indicateur_libelle(indic) -> str:
    """Helper d'affichage des indicateurs."""
    return (
        f"{indicateur_field(indic.taux_progression)}% "
        f"crédits={indicateur_field(indic.credits_acquis)}/{indicateur_field(indic.credits_total)}"
    )


def indicateur_field(valeur):
    return f"{valeur:.1f}" if isinstance(valeur, (int, float)) and valeur is not None else "—"
