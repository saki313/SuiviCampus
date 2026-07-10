"""ViewSets académiques (BF01, BF05, BF07) — UE, Semestre, Parcours, Résultats."""
from rest_framework import viewsets, permissions

from apps.academics.models import (
    UniteEnseignement, Semestre, ParcoursAcademique,
    ResultatAcademique, HistoriqueAcademique, Presence,
)
from apps.academics.serializers import (
    UniteEnseignementSerializer, SemestreSerializer, ParcoursAcademiqueSerializer,
    ResultatAcademiqueSerializer, HistoriqueAcademiqueSerializer, PresenceSerializer,
)
from apps.accounts.permissions import IsStaffOrAdmin


class UniteEnseignementViewSet(viewsets.ModelViewSet):
    queryset = UniteEnseignement.objects.all()
    serializer_class = UniteEnseignementSerializer
    filterset_fields = ["semestre_numero", "ue_type"]
    search_fields = ["code", "intitule"]
    ordering_fields = ["code", "credits", "semestre_numero"]


class SemestreViewSet(viewsets.ModelViewSet):
    queryset = Semestre.objects.all()
    serializer_class = SemestreSerializer
    filterset_fields = ["numero", "annee", "annee_scolaire"]
    ordering_fields = ["annee", "numero"]


class ParcoursAcademiqueViewSet(viewsets.ModelViewSet):
    queryset = ParcoursAcademique.objects.select_related("etudiant").all()
    serializer_class = ParcoursAcademiqueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["filiere", "niveau", "statut", "annee_scolaire"]
    search_fields = ["etudiant__matricule"]
    ordering_fields = ["created_at", "etudiant__matricule"]


class ResultatAcademiqueViewSet(viewsets.ModelViewSet):
    queryset = ResultatAcademique.objects.select_related(
        "etudiant", "ue", "semestre"
    ).all()
    serializer_class = ResultatAcademiqueSerializer
    filterset_fields = ["etudiant", "ue", "semestre", "valide", "session"]
    search_fields = ["etudiant__matricule", "ue__code", "ue__intitule"]
    ordering_fields = ["note", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Un étudiant ne voit que ses propres résultats
        if user.is_authenticated and user.role == "etudiant":
            qs = qs.filter(etudiant__utilisateur=user)
        return qs


class HistoriqueAcademiqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique consolidé (BF07) — lecture seule via API."""
    queryset = HistoriqueAcademique.objects.select_related("etudiant", "semestre").all()
    serializer_class = HistoriqueAcademiqueSerializer
    filterset_fields = ["etudiant", "semestre"]
    search_fields = ["etudiant__matricule"]
    ordering_fields = ["-semestre__annee", "etudiant__matricule"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == "etudiant":
            qs = qs.filter(etudiant__utilisateur=user)
        return qs


class PresenceViewSet(viewsets.ModelViewSet):
    queryset = Presence.objects.select_related("etudiant", "ue").all()
    serializer_class = PresenceSerializer
    permission_classes = [IsStaffOrAdmin]
    filterset_fields = ["etudiant", "ue", "present", "date_cours"]
    ordering_fields = ["date_cours"]
