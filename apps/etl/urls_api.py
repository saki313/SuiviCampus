"""Routes API REST — ETL (BF11)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.etl.api.views import EtlRunViewSet

router = DefaultRouter()
router.register("etl/runs", EtlRunViewSet, basename="etl-run")

app_name = "etl_api"
urlpatterns = [
    path("", include(router.urls)),
]
