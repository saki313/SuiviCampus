"""ViewSets des alertes (BF04) — consultation + traitement.

Traitement (passage à "Traitée") : délègue au service alerts.services.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.alerts.models import Alerte, ParametreAlerte, Recommandation
from apps.alerts.serializers import (
    AlerteSerializer, ParametreAlerteSerializer, RecommandationSerializer,
)
from apps.alerts.services import traiter_alerte
from apps.accounts.permissions import IsAdministrateur, IsStaffOrAdmin


class AlerteViewSet(viewsets.ReadOnlyModelViewSet):
    """Consultation des alertes académiques (BF04).

    Le traitement (traiter/archiver) se fait via actions dédiées qui
    délèguent au service.
    """
    queryset = Alerte.objects.select_related(
        "etudiant__utilisateur", "traitee_par"
    ).prefetch_related("recommandations").all()
    serializer_class = AlerteSerializer
    filterset_fields = ["etudiant", "type", "niveau_risque", "statut"]
    search_fields = ["etudiant__matricule", "message"]
    ordering_fields = ["created_at", "niveau_risque", "score_risque"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Un étudiant ne voit que ses propres alertes
        if user.is_authenticated and user.role == "etudiant":
            qs = qs.filter(etudiant__utilisateur=user)
        return qs

    @action(detail=True, methods=["post"], url_path="traiter")
    def traiter(self, request, pk=None):
        """Marque une alerte comme traitée par l'utilisateur courant."""
        alerte = self.get_object()
        traiter_alerte(alerte, request.user)
        return Response(AlerteSerializer(alerte).data)

    @action(
        detail=False, methods=["post"],
        permission_classes=[IsAdministrateur],
        url_path="archiver-anciennes",
    )
    def archiver_anciennes(self, request):
        """Archive les alertes traitées de plus de 90 jours."""
        from apps.alerts.services import archiver_anciennes_alertes
        jours = int(request.data.get("jours", 90))
        count = archiver_anciennes_alertes(jours)
        return Response({"detail": f"{count} alertes archivées."})


class ParametreAlerteViewSet(viewsets.ModelViewSet):
    """Gestion des paramètres d'alerte (BF13) — Administrateur uniquement."""
    queryset = ParametreAlerte.objects.all()
    serializer_class = ParametreAlerteSerializer
    permission_classes = [IsAdministrateur]


class RecommandationViewSet(viewsets.ReadOnlyModelViewSet):
    """Consultation des recommandations pédagogiques (DS2)."""
    queryset = Recommandation.objects.select_related("alerte").all()
    serializer_class = RecommandationSerializer
    filterset_fields = ["alerte", "priorite"]
