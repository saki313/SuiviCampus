"""Modeles des alertes — Alerte, ParametreAlerte, Recommandation (memoire §A.1).

BF04 : Generation et notification d'alertes academiques.
BF13 : Parametrage des seuils et regles d'alerte (Administrateur).

Flux (DS2) : GestionnaireAlertes -> ParametreAlerte (seuils) -> Alerte ->
              notification Etudiant/Responsable -> Recommandation -> archive.
"""
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.enums import NiveauRisque, StatutAlerte, TypeAlerte
from apps.accounts.models import ProfilEtudiant


class ParametreAlerte(TimeStampedModel):
    """Parametres configurables des seuils d'alerte (BF13).

    Stocke les seuils de declenchement et les ponderations du score de risque
    (Eq 2.1) pour calibration future (D6).
    """
    seuil_faible = models.FloatField(
        "Seuil Faible", default=30.0,
        help_text="Score <= seuil_faible => risque Faible"
    )
    seuil_modere = models.FloatField(
        "Seuil Modere", default=60.0,
        help_text="Score <= seuil_modere => risque Modere ; > => Eleve"
    )
    ponderation_notes = models.FloatField("Ponderation N (notes)", default=0.40)
    ponderation_credits = models.FloatField("Ponderation C (credits)", default=0.30)
    ponderation_ue_echec = models.FloatField("Ponderation U (UE echec)", default=0.20)
    ponderation_absenteisme = models.FloatField("Ponderation A (absenteisme)", default=0.10)
    active = models.BooleanField("Actif", default=True)

    class Meta:
        db_table = "parametre_alerte"
        verbose_name = "Parametre d'alerte"
        verbose_name_plural = "Parametres d'alerte"

    def __str__(self):
        return f"Alerte: seuils {self.seuil_faible}/{self.seuil_modere}"


class Alerte(TimeStampedModel):
    """Alerte academique generee automatiquement ou manuellement (BF04).

    Attributs (memoire §A.1) : type, niveauRisque, statut, etudiant, message.
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="alertes", verbose_name="Etudiant",
    )
    type = models.CharField("Type", max_length=50, choices=TypeAlerte.choices, default=TypeAlerte.RISQUE)
    niveau_risque = models.CharField(
        "Niveau de risque", max_length=10, choices=NiveauRisque.choices, default=NiveauRisque.MODERE
    )
    statut = models.CharField(
        "Statut", max_length=15, choices=StatutAlerte.choices, default=StatutAlerte.ACTIVE
    )
    score_risque = models.FloatField("Score au moment de l'alerte", null=True, blank=True)
    message = models.TextField("Message", blank=True, default="")
    traitee_par = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Traitee par",
    )
    date_traitement = models.DateTimeField("Date de traitement", null=True, blank=True)

    class Meta:
        db_table = "alerte"
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["etudiant", "statut"], name="idx_alerte_etu_statut"),
            models.Index(fields=["niveau_risque"], name="idx_alerte_niveau"),
        ]

    def __str__(self):
        return f"[{self.niveau_risque}] {self.etudiant.matricule} — {self.type}"


class Recommandation(TimeStampedModel):
    """Recommandation pedagogique associee a une alerte (DS2).

    Generee par le gestionnaire d'alertes apres detection d'un risque.
    """
    alerte = models.ForeignKey(
        Alerte, on_delete=models.CASCADE,
        related_name="recommandations", verbose_name="Alerte",
    )
    description = models.TextField("Description", blank=True, default="")
    priorite = models.CharField(
        "Priorite", max_length=10,
        choices=[("haute", "Haute"), ("moyenne", "Moyenne"), ("basse", "Basse")],
        default="moyenne",
    )

    class Meta:
        db_table = "recommandation"
        verbose_name = "Recommandation"
        verbose_name_plural = "Recommandations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reco: {self.priorite} pour alerte #{self.alerte_id}"
