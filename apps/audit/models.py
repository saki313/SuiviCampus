"""Modele de journal d'audit — tracabilite des actions sensibles (BF securite).

Enregistre les mutations API, connexions, actions admin.
"""
from django.db import models

from apps.common.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    """Journal d'audit — tracee des actions sur la plateforme."""
    utilisateur = models.CharField("Utilisateur", max_length=150, blank=True, default="")
    action = models.CharField("Action (HTTP)", max_length=10, blank=True, default="")
    chemin = models.CharField("Chemin", max_length=255, blank=True, default="")
    adresse_ip = models.GenericIPAddressField("Adresse IP", null=True, blank=True)
    statut = models.PositiveSmallIntegerField("Statut HTTP", null=True, blank=True)
    detail = models.TextField("Detail", blank=True, default="")

    class Meta:
        db_table = "audit_log"
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["utilisateur", "-created_at"], name="idx_audit_user_time"),
        ]

    def __str__(self):
        return f"[{self.action}] {self.utilisateur} {self.chemin} ({self.statut})"
