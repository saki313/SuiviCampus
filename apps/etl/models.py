"""Modèles ETL — suivi des exécutions (synchronisation différentielle, reprise).

Stocke l'historique des runs ETL pour :
  - la synchronisation différentielle (dernier timestamp extrait)
  - la reprise après échec (reprendre à partir du dernier run réussi)
  - les logs d'audit (BF11)
"""
from django.db import models

from apps.common.models import TimeStampedModel


class EtlRun(TimeStampedModel):
    """Journal d'une exécution ETL (BF11).

    Un run = une synchronisation complète (extract → transform → load).
    """

    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        SUCCES = "succes", "Succès"
        ECHEC = "echec", "Échec"
        PARTIEL = "partiel", "Partiel"

    STATUT_CHOICES = Statut.choices  # rétro-compatibilité

    statut = models.CharField(
        "Statut", max_length=15, choices=STATUT_CHOICES, default=Statut.EN_COURS
    )
    source_mode = models.CharField("Mode source", max_length=10, default="mock")
    date_debut = models.DateTimeField("Date de début", auto_now_add=True)
    date_fin = models.DateTimeField("Date de fin", null=True, blank=True)
    # Marqueur de synchro différentielle : timestamp de la dernière extraction réussie
    dernier_since = models.CharField(
        "Dernier 'since' traité", max_length=30, blank=True, default=""
    )

    # Compteurs
    nb_etudiants_extraits = models.PositiveIntegerField("Étudiants extraits", default=0)
    nb_ue_extraits = models.PositiveIntegerField("UE extraits", default=0)
    nb_resultats_extraits = models.PositiveIntegerField("Résultats extraits", default=0)
    nb_presences_extraites = models.PositiveIntegerField("Présences extraites", default=0)

    nb_etudiants_charges = models.PositiveIntegerField("Étudiants chargés", default=0)
    nb_ue_charges = models.PositiveIntegerField("UE chargés", default=0)
    nb_resultats_charges = models.PositiveIntegerField("Résultats chargés", default=0)

    nb_erreurs = models.PositiveIntegerField("Erreurs", default=0)
    log = models.TextField("Journal détaillé", blank=True, default="")

    class Meta:
        db_table = "etl_run"
        verbose_name = "Exécution ETL"
        verbose_name_plural = "Exécutions ETL"
        ordering = ["-date_debut"]

    def __str__(self):
        return f"ETL #{self.id} [{self.statut}] {self.date_debut:%Y-%m-%d %H:%M}"

    def ajouter_log(self, message: str) -> None:
        """Ajoute une ligne au journal."""
        self.log = f"{self.log}{message}\n"
        self.save(update_fields=["log", "updated_at"])


class EtlCheckpoint(TimeStampedModel):
    """Curseur de synchronisation différentielle (mémoire §3.2.2).

    Mémorise le dernier point d'extraction par type de ressource, afin de
    ne recharger que les modifications depuis la dernière synchro réussie.
    """
    ressource = models.CharField("Ressource", max_length=30, unique=True)
    derniere_synchro = models.DateTimeField("Dernière synchronisation", null=True, blank=True)
    nb_total_synchro = models.PositiveIntegerField("Nb total synchronisé", default=0)

    class Meta:
        db_table = "etl_checkpoint"
        verbose_name = "Point de synchronisation ETL"
        verbose_name_plural = "Points de synchronisation ETL"

    def __str__(self):
        return f"Checkpoint {self.ressource} @ {self.derniere_synchro}"


class EtlExecutionErreur(TimeStampedModel):
    """Journal structuré des erreurs d'une exécution ETL (reprise après échec)."""
    run = models.ForeignKey(
        EtlRun, on_delete=models.CASCADE,
        related_name="erreurs_log", verbose_name="Exécution",
    )
    etape = models.CharField("Étape", max_length=30, default="")  # extract/transform/load
    ressource = models.CharField("Ressource", max_length=50, blank=True, default="")
    message = models.TextField("Message d'erreur")

    class Meta:
        db_table = "etl_erreur"
        verbose_name = "Erreur ETL"
        verbose_name_plural = "Erreurs ETL"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.etape}] {self.message[:80]}"
