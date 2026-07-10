"""Serializers analytiques — IndicateurAcademique (KPI calculés)."""
from rest_framework import serializers

from apps.analytics.models import IndicateurAcademique


class IndicateurAcademiqueSerializer(serializers.ModelSerializer):
    """Indicateurs académiques d'un étudiant (BF02, BF03, BF06)."""
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)
    etudiant_nom = serializers.CharField(
        source="etudiant.utilisateur.get_full_name", read_only=True
    )

    class Meta:
        model = IndicateurAcademique
        fields = "__all__"
        read_only_fields = [
            "id", "created_at", "updated_at",
            "score_risque", "classification_risque", "taux_progression",
            "moyenne_generale", "credits_acquis", "credits_total",
            "ues_echec", "ues_total", "taux_absenteisme",
            "semestres_restants", "proj_diplomation",
        ]
