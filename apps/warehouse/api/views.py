"""ViewSets du Data Warehouse — accès en lecture au schéma en étoile."""
from rest_framework import viewsets

from apps.warehouse.models import (
    DimEtudiant, DimUE, DimSemestre, DimTemps, FaitResultats,
)
from apps.warehouse.serializers import (
    DimEtudiantSerializer, DimUESerializer, DimSemestreSerializer,
    DimTempsSerializer, FaitResultatsSerializer,
)


class DimEtudiantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimEtudiant.objects.all()
    serializer_class = DimEtudiantSerializer
    filterset_fields = ["niveau_actuel", "filiere", "promotion"]
    search_fields = ["matricule"]


class DimUEViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimUE.objects.all()
    serializer_class = DimUESerializer
    filterset_fields = ["semestre"]
    search_fields = ["code", "intitule"]


class DimSemestreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimSemestre.objects.all()
    serializer_class = DimSemestreSerializer
    filterset_fields = ["numero", "annee"]


class DimTempsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimTemps.objects.all()
    serializer_class = DimTempsSerializer
    filterset_fields = ["annee", "session_examen", "annee_scolaire"]


class FaitResultatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Table de faits centrale (lecture analytique)."""
    queryset = FaitResultats.objects.select_related(
        "etudiant", "ue", "semestre", "temps"
    ).all()
    serializer_class = FaitResultatsSerializer
    filterset_fields = ["etudiant", "ue", "semestre", "temps", "valide"]
    search_fields = ["etudiant__matricule", "ue__code"]
    ordering_fields = ["note", "score_risque", "created_at"]
