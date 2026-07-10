"""ViewSets analytiques — IndicateurAcademique (BF03) + trigger recalcul."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.models import IndicateurAcademique
from apps.analytics.serializers import IndicateurAcademiqueSerializer
from apps.analytics.services import calculer_indicateurs_etudiant
from apps.accounts.models import ProfilEtudiant
from apps.accounts.permissions import IsStaffOrAdmin


class IndicateurAcademiqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Consultation des indicateurs académiques calculés (BF03)."""
    queryset = IndicateurAcademique.objects.select_related(
        "etudiant__utilisateur"
    ).all()
    serializer_class = IndicateurAcademiqueSerializer
    filterset_fields = ["etudiant", "classification_risque", "semestre"]
    search_fields = ["etudiant__matricule"]
    ordering_fields = ["score_risque", "taux_progression", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Un étudiant ne voit que ses propres indicateurs
        if user.is_authenticated and user.role == "etudiant":
            qs = qs.filter(etudiant__utilisateur=user, semestre=None)
        return qs

    @action(
        detail=False, methods=["post"],
        permission_classes=[IsStaffOrAdmin],
        url_path="recalculer",
    )
    def recalculer(self, request):
        """Recalcule les indicateurs d'un étudiant (ou de toute la promotion).

        Body optionnel : {"etudiant_id": 123}
        """
        etudiant_id = request.data.get("etudiant_id")
        if etudiant_id:
            try:
                etudiant = ProfilEtudiant.objects.get(id=etudiant_id)
            except ProfilEtudiant.DoesNotExist:
                return Response(
                    {"detail": "Étudiant introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            calculer_indicateurs_etudiant(etudiant)
            return Response({"detail": f"Indicateurs recalculés pour {etudiant.matricule}."})
        # Sinon : recalcul global
        from apps.analytics.services import calculer_indicateurs_promotion
        count = calculer_indicateurs_promotion()
        return Response({"detail": f"{count} étudiants recalculés."})
