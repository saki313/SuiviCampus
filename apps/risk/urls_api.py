"""Routes API REST — Module risque (BF02, BF10)."""
from django.urls import path

from apps.risk.api.views import (
    ScoreRisqueView, DistributionRisqueView, UECritiquesView,
)

app_name = "risk_api"
urlpatterns = [
    path("risk/scores/", ScoreRisqueView.as_view(), name="score-liste"),
    path("risk/scores/<str:matricule>/", ScoreRisqueView.as_view(), name="score-detail"),
    path("risk/distribution/", DistributionRisqueView.as_view(), name="distribution"),
    path("risk/ue-critiques/", UECritiquesView.as_view(), name="ue-critiques"),
]
