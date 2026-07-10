"""Serializers des alertes — Alerte, ParametreAlerte, Recommandation."""
from rest_framework import serializers

from apps.alerts.models import Alerte, ParametreAlerte, Recommandation


class RecommandationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommandation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AlerteSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)
    etudiant_nom = serializers.CharField(
        source="etudiant.utilisateur.get_full_name", read_only=True
    )
    recommandations = RecommandationSerializer(many=True, read_only=True)

    class Meta:
        model = Alerte
        fields = "__all__"
        read_only_fields = [
            "id", "created_at", "updated_at",
            "score_risque", "message", "traitee_par", "date_traitement",
        ]


class ParametreAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametreAlerte
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
