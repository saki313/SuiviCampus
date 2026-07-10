"""Vues API du module risque — score de risque (BF02) + UE critiques (BF10).

Ces vues délèguent entièrement au service apps.risk.services ; aucune
logique métier ici.
"""
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import ProfilEtudiant
from apps.risk.services import (
    get_score_etudiant,
    get_distribution_scores,
    get_ue_critiques,
)
from apps.risk.serializers import (
    ScoreRisqueSerializer, DistributionRisqueSerializer, UECritiqueSerializer,
)


class ScoreRisqueView(views.APIView):
    """GET /api/risk/scores/?etudiant_id= ou /api/risk/scores/<matricule>/.

    Sans paramètre : score de l'étudiant connecté (si étudiant).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, matricule=None):
        user = request.user
        # Détermine l'étudiant cible
        if matricule:
            if user.role == "etudiant":
                # Un étudiant ne consulte que son propre score
                if not user._profil_etudiant or user._profil_etudiant.matricule != matricule:
                    return Response(
                        {"detail": "Accès non autorisé."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            try:
                etudiant = ProfilEtudiant.objects.get(matricule=matricule)
            except ProfilEtudiant.DoesNotExist:
                return Response(
                    {"detail": "Étudiant introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Pas de matricule → étudiant connecté
            if user.role != "etudiant":
                return Response(
                    {"detail": "Précisez un matricule ou connectez-vous en tant qu'étudiant."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            etudiant = getattr(user, "_profil_etudiant", None)
            if etudiant is None:
                return Response(
                    {"detail": "Profil étudiant introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        data = get_score_etudiant(etudiant)
        return Response(ScoreRisqueSerializer(data).data)


class DistributionRisqueView(views.APIView):
    """GET /api/risk/distribution/?filiere=&niveau= — BF03 TB Responsable."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filiere = request.query_params.get("filiere")
        niveau = request.query_params.get("niveau")
        data = get_distribution_scores(filiere, niveau)
        return Response(DistributionRisqueSerializer(data).data)


class UECritiquesView(views.APIView):
    """GET /api/risk/ue-critiques/?filiere=&niveau=&limite= — BF10."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filiere = request.query_params.get("filiere")
        niveau = request.query_params.get("niveau")
        limite = int(request.query_params.get("limite", 10))
        data = get_ue_critiques(filiere, niveau, limite)
        return Response(UECritiqueSerializer(data, many=True).data)
