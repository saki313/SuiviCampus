"""Routes API REST — Alertes (BF04, BF13)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.alerts.api.views import (
    AlerteViewSet, ParametreAlerteViewSet, RecommandationViewSet,
)

router = DefaultRouter()
router.register("alertes", AlerteViewSet, basename="alerte")
router.register("parametres-alerte", ParametreAlerteViewSet, basename="parametre-alerte")
router.register("recommandations", RecommandationViewSet, basename="recommandation")

app_name = "alerts_api"
urlpatterns = [
    path("", include(router.urls)),
]
