"""Modeles analytiques — indicateurs calcules (memoire §2.4.3).

IndicateurAcademique : stocke les KPI calcules (score_risque, tx_progression,
proj_diplomation). Alimente les tableaux de bord (BF03).

Les attributs derives (/notation UML) sont marques ici : scoreRisque,
txProgression, projDiplomation.
"""
from django.db import models

from apps.common.models import TimeStampedModel
from apps.accounts.models import ProfilEtudiant
from apps.academics.models import Semestre


class IndicateurAcademique(TimeStampedModel):
    """Indicateurs academiques calcules pour un etudiant / semestre (BF02, BF06).

    Attributs derives (notation / du diagramme de classes) :
        /scoreRisque : Eq 2.1, [0-100]
        /txProgression : Eq 2.2, [%]
        /projDiplomation : date estimee
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="indicateurs", verbose_name="Etudiant",
    )
    semestre = models.ForeignKey(
        Semestre, on_delete=models.PROTECT,
        related_name="indicateurs", verbose_name="Semestre",
        null=True, blank=True,
    )

    # Indicateurs derives (calcules par le moteur KPI)
    moyenne_generale = models.DecimalField(
        "Moyenne generale /20", max_digits=5, decimal_places=2, null=True, blank=True
    )
    score_risque = models.FloatField(
        "Score de risque [0-100]", null=True, blank=True
    )
    classification_risque = models.CharField(
        "Classification", max_length=10,
        choices=[("Faible", "Faible"), ("Modere", "Modere"), ("Eleve", "Eleve")],
        blank=True, default="",
    )
    taux_progression = models.FloatField(
        "Taux de progression [%]", null=True, blank=True
    )
    credits_acquis = models.PositiveIntegerField("Credits acquis", default=0)
    credits_total = models.PositiveIntegerField("Credits total vises", default=0)
    ues_echec = models.PositiveSmallIntegerField("UEs en echec", default=0)
    ues_total = models.PositiveSmallIntegerField("UEs total", default=0)
    taux_absenteisme = models.FloatField("Taux d'absenteisme [%]", null=True, blank=True)
    semestres_restants = models.FloatField("Semestres restants estimes", null=True, blank=True)
    proj_diplomation = models.DateField(
        "Projection de diplomation", null=True, blank=True
    )

    class Meta:
        db_table = "indicateur_academique"
        verbose_name = "Indicateur academique"
        verbose_name_plural = "Indicateurs academiques"
        ordering = ["etudiant__matricule", "-created_at"]
        indexes = [
            models.Index(fields=["score_risque"], name="idx_indicateur_score"),
            # Lookup direct (etudiant, semestre=None) très fréquent : dashboards,
            # services analytics/risk/alerts, recalcul KPI (Eq 2.1/2.2).
            models.Index(fields=["etudiant", "semestre"], name="idx_indic_etu_sem"),
            # Filtrage TB responsables (BF03) : distribution par classification.
            models.Index(fields=["classification_risque", "semestre"], name="idx_indic_class_sem"),
        ]

    def __str__(self):
        return f"Indic. {self.etudiant.matricule} score={self.score_risque}"
