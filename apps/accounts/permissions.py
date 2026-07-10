"""Permissions RBAC par rôle (BF12) — contrôle d'accès fin.

Hiérarchie des rôles (mémoire §2.1.1) :
    - étudiant          : accès à SES données uniquement
    - enseignant        : accès aux étudiants qu'il suit
    - responsable       : accès à sa promotion + rapports + gestion alertes
    - administrateur    : accès complet (ETL, comptes, paramètres, audit)

Utilise le champ `role` du modèle Utilisateur + vérifications métier.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_role(user, *roles):
    """Vérifie si l'utilisateur a l'un des rôles donnés."""
    return bool(user and user.is_authenticated and user.role in roles)


class IsEtudiant(BasePermission):
    """L'utilisateur est un étudiant."""
    def has_permission(self, request, view):
        return _is_role(request.user, "etudiant")


class IsEnseignant(BasePermission):
    """L'utilisateur est un enseignant (ou responsable — hérite)."""
    def has_permission(self, request, view):
        return _is_role(request.user, "enseignant", "responsable")


class IsResponsable(BasePermission):
    """L'utilisateur est un responsable pédagogique."""
    def has_permission(self, request, view):
        return _is_role(request.user, "responsable")


class IsAdministrateur(BasePermission):
    """L'utilisateur est un administrateur."""
    def has_permission(self, request, view):
        return _is_role(request.user, "administrateur")


class IsStaffOrAdmin(BasePermission):
    """Administrateur OU responsable (rôles avec pouvoir de gestion)."""
    def has_permission(self, request, view):
        return _is_role(request.user, "responsable", "administrateur") or (
            bool(request.user and request.user.is_authenticated and request.user.is_staff)
        )


class IsOwnerOrReadOnly(BasePermission):
    """Un étudiant ne voit que ses propres données ; lecture seule sinon."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Un utilisateur modifie uniquement ce qui lui appartient
        if hasattr(obj, "utilisateur"):
            return obj.utilisateur == request.user
        if hasattr(obj, "etudiant") and hasattr(obj.etudiant, "utilisateur"):
            return obj.etudiant.utilisateur == request.user
        return False


class ReadOnly(BasePermission):
    """Accès en lecture seule pour tous les authentifiés."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.method in SAFE_METHODS
        )
