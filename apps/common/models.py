"""Modèles de base partagés — mixin timestamp, modèle abstrait.

Toutes les entités métier héritent de TimeStampedModel pour l'audit
(created_at / updated_at) automatique.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Mixin : horodatage automatique de création et dernière modification."""

    created_at = models.DateTimeField(
        "Date de création", auto_now_add=True, db_index=True
    )
    updated_at = models.DateTimeField(
        "Dernière modification", auto_now=True
    )

    class Meta:
        abstract = True
