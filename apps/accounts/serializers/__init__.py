"""Serializers des comptes (BF12).

RÈGLE D'OR : aucune logique métier ici — uniquement la sérialisation.
Les mutations complexes passent par les services.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import (
    Utilisateur,
    ProfilEtudiant,
    ProfilEnseignant,
    ResponsablePedagogique,
    ProfilAdministrateur,
)


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer de base d'un utilisateur (lecture)."""

    class Meta:
        model = Utilisateur
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "telephone", "role", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """Création d'utilisateur (inscription / admin) — avec mot de passe."""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "telephone", "role", "password", "password2",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfilEtudiantSerializer(serializers.ModelSerializer):
    """Profil étudiant — inclut le nom de l'utilisateur lié."""
    utilisateur_nom = serializers.CharField(source="utilisateur.get_full_name", read_only=True)
    utilisateur_email = serializers.CharField(source="utilisateur.email", read_only=True)

    class Meta:
        model = ProfilEtudiant
        fields = [
            "id", "utilisateur", "utilisateur_nom", "utilisateur_email",
            "matricule", "niveau", "filiere", "promotion", "annee_scolaire",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProfilEnseignantSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.get_full_name", read_only=True)

    class Meta:
        model = ProfilEnseignant
        fields = [
            "id", "utilisateur", "utilisateur_nom",
            "departement", "specialite", "grade", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ResponsablePedagogiqueSerializer(serializers.ModelSerializer):
    enseignant_nom = serializers.CharField(
        source="enseignant.utilisateur.get_full_name", read_only=True
    )

    class Meta:
        model = ResponsablePedagogique
        fields = [
            "id", "enseignant", "enseignant_nom",
            "filiere_geree", "niveau_gere", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProfilAdministrateurSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.get_full_name", read_only=True)

    class Meta:
        model = ProfilAdministrateur
        fields = ["id", "utilisateur", "utilisateur_nom", "service", "created_at"]
        read_only_fields = ["id", "created_at"]
