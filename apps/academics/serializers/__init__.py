"""Serializers académiques — UE, Semestre, Parcours, Résultat, Historique.

Aucune logique métier : sérialisation uniquement.
"""
from rest_framework import serializers

from apps.academics.models import (
    UniteEnseignement,
    Semestre,
    ParcoursAcademique,
    ResultatAcademique,
    HistoriqueAcademique,
    Presence,
)


class UniteEnseignementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniteEnseignement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class SemestreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semestre
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ParcoursAcademiqueSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)

    class Meta:
        model = ParcoursAcademique
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ResultatAcademiqueSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)
    ue_code = serializers.CharField(source="ue.code", read_only=True)
    semestre_label = serializers.CharField(read_only=True)

    class Meta:
        model = ResultatAcademique
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_semestre_label(self, obj):
        return str(obj.semestre)


class HistoriqueAcademiqueSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)

    class Meta:
        model = HistoriqueAcademique
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PresenceSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)
    ue_code = serializers.CharField(source="ue.code", read_only=True)

    class Meta:
        model = Presence
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
