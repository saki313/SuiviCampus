"""ViewSets des comptes (BF12) — gestion utilisateurs et profils.

Permissions : Administrateur = CRUD complet ; autres = lecture de leur profil.
"""
from rest_framework import viewsets, permissions

from apps.accounts.models import (
    Utilisateur,
    ProfilEtudiant,
    ProfilEnseignant,
    ResponsablePedagogique,
    ProfilAdministrateur,
)
from apps.accounts.permissions import IsAdministrateur, IsOwnerOrReadOnly
from apps.accounts.serializers import (
    UtilisateurSerializer,
    UtilisateurCreateSerializer,
    ProfilEtudiantSerializer,
    ProfilEnseignantSerializer,
    ResponsablePedagogiqueSerializer,
    ProfilAdministrateurSerializer,
)


class UtilisateurViewSet(viewsets.ModelViewSet):
    """Gestion des comptes utilisateurs (BF12)."""
    queryset = Utilisateur.objects.all()

    def get_serializer_class(self):
        if self.action in ("create",):
            return UtilisateurCreateSerializer
        return UtilisateurSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdministrateur()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Un étudiant ne voit que son propre compte ; admin voit tout
        user = self.request.user
        if user.role == "administrateur" or user.is_staff:
            return Utilisateur.objects.all()
        return Utilisateur.objects.filter(id=user.id)


class ProfilEtudiantViewSet(viewsets.ModelViewSet):
    queryset = ProfilEtudiant.objects.select_related("utilisateur").all()
    serializer_class = ProfilEtudiantSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            from apps.accounts.permissions import IsStaffOrAdmin
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Un étudiant ne voit que son propre profil
        if user.role == "etudiant":
            qs = qs.filter(utilisateur=user)
        return qs

    filterset_fields = ["niveau", "filiere", "promotion", "annee_scolaire"]
    search_fields = ["matricule", "utilisateur__first_name", "utilisateur__last_name"]
    ordering_fields = ["matricule", "niveau", "created_at"]


class ProfilEnseignantViewSet(viewsets.ModelViewSet):
    queryset = ProfilEnseignant.objects.select_related("utilisateur").all()
    serializer_class = ProfilEnseignantSerializer
    permission_classes = [IsOwnerOrReadOnly | IsAdministrateur]
    filterset_fields = ["departement", "specialite", "grade"]
    search_fields = ["utilisateur__first_name", "utilisateur__last_name"]


class ResponsablePedagogiqueViewSet(viewsets.ModelViewSet):
    queryset = ResponsablePedagogique.objects.select_related(
        "enseignant__utilisateur"
    ).all()
    serializer_class = ResponsablePedagogiqueSerializer
    permission_classes = [IsAdministrateur]
    filterset_fields = ["filiere_geree", "niveau_gere"]


class ProfilAdministrateurViewSet(viewsets.ModelViewSet):
    queryset = ProfilAdministrateur.objects.select_related("utilisateur").all()
    serializer_class = ProfilAdministrateurSerializer
    permission_classes = [IsAdministrateur]
