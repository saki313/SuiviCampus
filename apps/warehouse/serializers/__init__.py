"""Serializers du Data Warehouse — tables Dim_* et Fait_Resultats."""
from rest_framework import serializers

from apps.warehouse.models import (
    DimEtudiant, DimUE, DimSemestre, DimTemps, FaitResultats,
)


class DimEtudiantSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimEtudiant
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DimUESerializer(serializers.ModelSerializer):
    class Meta:
        model = DimUE
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DimSemestreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimSemestre
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DimTempsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimTemps
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FaitResultatsSerializer(serializers.ModelSerializer):
    etudiant_matricule = serializers.CharField(source="etudiant.matricule", read_only=True)
    ue_code = serializers.CharField(source="ue.code", read_only=True)

    class Meta:
        model = FaitResultats
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
