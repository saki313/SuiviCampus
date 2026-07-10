"""Modèles de comptes — Acteurs du MCD (diagramme de classes §2.2.2).

Hiérarchie d'héritage fidèle au diagramme de classes :
    Utilisateur (abstract, custom user)
    ├── Etudiant          → profil lié 1:1
    ├── Enseignant        → profil lié 1:1
    │   └── ResponsablePedagogique   (un responsable EST un enseignant)
    └── Administrateur    → profil lié 1:1

Le RBAC est géré via les groupes Django + permissions.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.enums import NiveauLMD


class Utilisateur(AbstractUser):
    """Classe mère abstraite des acteurs (mémoire §2.2.2).

    Champs communs à tous les acteurs : identifiants auth + téléphone + role.
    Les profils spécifiques (Etudiant, Enseignant, etc.) sont des tables
    liées par OneToOneField, permettant une requête directe sur le profil
    sans jointure multiple.
    """

    telephone = models.CharField(
        "Téléphone", max_length=20, blank=True, default=""
    )
    ROLE_CHOICES = [
        ("etudiant", "Étudiant"),
        ("enseignant", "Enseignant"),
        ("responsable", "Responsable pédagogique"),
        ("administrateur", "Administrateur"),
    ]
    role = models.CharField(
        "Rôle", max_length=20, choices=ROLE_CHOICES, default="etudiant"
    )

    class Meta:
        db_table = "utilisateur"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["last_name", "first_name", "username"]

    def __str__(self):
        full = self.get_full_name()
        return full or self.username

    # Propriétés de commodité pour accéder au profil lié
    @property
    def profil_etudiant(self):
        return getattr(self, "_profil_etudiant", None)

    @property
    def profil_enseignant(self):
        return getattr(self, "_profil_enseignant", None)

    @property
    def profil_administrateur(self):
        return getattr(self, "_profil_administrateur", None)


class ProfilEtudiant(TimeStampedModel):
    """Profil étudiant — lié 1:1 à Utilisateur (mémoire §A.1).

    Attributs : matricule, niveauActuel (LMD), filiere, promotion, anneeScolaire.
    """
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name="_profil_etudiant",
        verbose_name="Utilisateur",
    )
    matricule = models.CharField(
        "Matricule", max_length=20, unique=True, db_index=True
    )
    niveau = models.CharField(
        "Niveau LMD", max_length=5, choices=NiveauLMD.choices, default=NiveauLMD.L1
    )
    filiere = models.CharField("Filière", max_length=100, blank=True, default="")
    promotion = models.CharField(
        "Promotion", max_length=20, blank=True, default=""
    )
    annee_scolaire = models.CharField(
        "Année scolaire", max_length=9, blank=True, default=""
    )  # format "2025-2026"

    class Meta:
        db_table = "profil_etudiant"
        verbose_name = "Profil étudiant"
        verbose_name_plural = "Profils étudiants"
        ordering = ["matricule"]

    def __str__(self):
        return f"{self.matricule} — {self.utilisateur}"


class ProfilEnseignant(TimeStampedModel):
    """Profil enseignant — lié 1:1 à Utilisateur.

    Attributs : département, specialite, grade.
    """
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name="_profil_enseignant",
        verbose_name="Utilisateur",
    )
    departement = models.CharField("Département", max_length=100, blank=True, default="")
    specialite = models.CharField("Spécialité", max_length=100, blank=True, default="")
    grade = models.CharField("Grade", max_length=50, blank=True, default="")

    class Meta:
        db_table = "profil_enseignant"
        verbose_name = "Profil enseignant"
        verbose_name_plural = "Profils enseignants"
        ordering = ["utilisateur__last_name"]

    def __str__(self):
        return f"Pr. {self.utilisateur}"


class ResponsablePedagogique(TimeStampedModel):
    """Responsable pédagogique — hérite d'Enseignant (diagramme de classes).

    Un responsable pédagogique EST un enseignant avec des responsabilités
    institutionnelles supplémentaires (filière gérée, niveau géré).
    Relation 1:1 vers ProfilEnseignant (pas vers Utilisateur directement).
    """
    enseignant = models.OneToOneField(
        ProfilEnseignant, on_delete=models.CASCADE,
        related_name="responsabilite",
        verbose_name="Enseignant",
    )
    filiere_geree = models.CharField("Filière gérée", max_length=100, blank=True, default="")
    niveau_gere = models.CharField(
        "Niveau géré", max_length=5, choices=NiveauLMD.choices, blank=True, default=""
    )

    class Meta:
        db_table = "responsable_pedagogique"
        verbose_name = "Responsable pédagogique"
        verbose_name_plural = "Responsables pédagogiques"

    def __str__(self):
        return f"Resp. {self.enseignant}"


class ProfilAdministrateur(TimeStampedModel):
    """Profil administrateur — lié 1:1 à Utilisateur."""
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name="_profil_administrateur",
        verbose_name="Utilisateur",
    )
    service = models.CharField("Service", max_length=100, blank=True, default="")

    class Meta:
        db_table = "profil_administrateur"
        verbose_name = "Profil administrateur"
        verbose_name_plural = "Profils administrateurs"

    def __str__(self):
        return f"Admin {self.utilisateur}"
