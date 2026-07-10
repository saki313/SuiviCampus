"""Serializers du module risque — vues analytiques (BF02, BF10)."""
from rest_framework import serializers


class ScoreRisqueSerializer(serializers.Serializer):
    """Score de risque d'un étudiant (adaptation du service risk)."""
    etudiant_id = serializers.IntegerField()
    matricule = serializers.CharField()
    score = serializers.FloatField()
    niveau = serializers.CharField()
    indicateurs = serializers.DictField()


class UECritiqueSerializer(serializers.Serializer):
    """UE présentant les plus fortes difficultés (BF10)."""
    code = serializers.CharField()
    intitule = serializers.CharField()
    credits = serializers.IntegerField()
    effectif = serializers.IntegerField()
    echecs = serializers.IntegerField()
    taux_echec = serializers.FloatField()
    moyenne = serializers.FloatField(allow_null=True)


class DistributionRisqueSerializer(serializers.Serializer):
    """Distribution des étudiants par niveau de risque."""
    Faible = serializers.IntegerField()
    Modere = serializers.IntegerField()
    Eleve = serializers.IntegerField()
