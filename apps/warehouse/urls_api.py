"""Routes API REST — Data Warehouse (lecture analytique)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.warehouse.api.views import (
    DimEtudiantViewSet, DimUEViewSet, DimSemestreViewSet,
    DimTempsViewSet, FaitResultatsViewSet,
)

router = DefaultRouter()
router.register("dw/etudiants", DimEtudiantViewSet, basename="dw-etudiant")
router.register("dw/ue", DimUEViewSet, basename="dw-ue")
router.register("dw/semestres", DimSemestreViewSet, basename="dw-semestre")
router.register("dw/temps", DimTempsViewSet, basename="dw-temps")
router.register("dw/faits", FaitResultatsViewSet, basename="dw-fait")

app_name = "warehouse_api"
urlpatterns = [
    path("", include(router.urls)),
]
