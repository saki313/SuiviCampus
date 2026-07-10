"""Routes API REST — Académique (BF01, BF05, BF07)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.academics.api.views import (
    UniteEnseignementViewSet, SemestreViewSet, ParcoursAcademiqueViewSet,
    ResultatAcademiqueViewSet, HistoriqueAcademiqueViewSet, PresenceViewSet,
)

router = DefaultRouter()
router.register("ue", UniteEnseignementViewSet, basename="ue")
router.register("semestres", SemestreViewSet, basename="semestre")
router.register("parcours", ParcoursAcademiqueViewSet, basename="parcours")
router.register("resultats", ResultatAcademiqueViewSet, basename="resultat")
router.register("historique", HistoriqueAcademiqueViewSet, basename="historique")
router.register("presences", PresenceViewSet, basename="presence")

app_name = "academics_api"
urlpatterns = [
    path("", include(router.urls)),
]
