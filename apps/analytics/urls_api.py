"""Routes API REST — Analytique & KPI (BF02, BF03, BF06)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.analytics.api.views import IndicateurAcademiqueViewSet

router = DefaultRouter()
router.register("indicateurs", IndicateurAcademiqueViewSet, basename="indicateur")

app_name = "analytics_api"
urlpatterns = [
    path("", include(router.urls)),
]
