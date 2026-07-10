"""Vues API ETL (BF11) — supervision et déclenchement de la synchronisation.

L'administrateur peut :
  - Lister l'historique des runs (GET /api/etl/runs/)
  - Consulter le détail d'un run + ses logs (GET /api/etl/runs/<id>/)
  - Déclencher un nouveau run (POST /api/etl/runs/lancer/)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, CharField

from apps.etl.models import EtlRun, EtlExecutionErreur
from apps.etl.services.pipeline import executer_etl
from apps.accounts.permissions import IsAdministrateur


class EtlRunSerializer(ModelSerializer):
    class Meta:
        model = EtlRun
        fields = [
            "id", "statut", "source_mode", "date_debut", "date_fin",
            "nb_etudiants_extraits", "nb_ue_extraits", "nb_resultats_extraits",
            "nb_presences_extraites", "nb_etudiants_charges", "nb_ue_charges",
            "nb_resultats_charges", "nb_erreurs", "log",
        ]
        read_only_fields = fields


class EtlExecutionErreurSerializer(ModelSerializer):
    class Meta:
        model = EtlExecutionErreur
        fields = ["id", "etape", "ressource", "message", "created_at"]


class EtlRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique et supervision des exécutions ETL (BF11)."""
    queryset = EtlRun.objects.all()
    serializer_class = EtlRunSerializer
    permission_classes = [IsAdministrateur]
    filterset_fields = ["statut", "source_mode"]
    ordering_fields = ["date_debut", "statut"]

    @action(detail=True, methods=["get"], url_path="erreurs")
    def erreurs(self, request, pk=None):
        """Liste les erreurs d'une exécution."""
        run = self.get_object()
        erreurs = run.erreurs_log.all()
        return Response(EtlExecutionErreurSerializer(erreurs, many=True).data)

    @action(
        detail=False, methods=["post"], url_path="lancer",
        permission_classes=[IsAdministrateur],
    )
    def lancer(self, request):
        """Déclenche un nouveau cycle ETL.

        Body optionnel : {"full": true} pour forcer une synchro complète.
        """
        full = request.data.get("full", False)
        try:
            run = executer_etl(differentiel=not full)
        except Exception as e:
            return Response(
                {"detail": f"Échec ETL : {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            EtlRunSerializer(run).data,
            status=status.HTTP_201_CREATED,
        )
