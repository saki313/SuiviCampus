"""Routes API REST — téléchargement des rapports (BF08).

Endpoints :
  GET /api/rapports/pdf/    → rapport PDF
  GET /api/rapports/excel/  → export Excel
  GET /api/rapports/csv/    → export CSV

Paramètres de requête (optionnels) :
  filiere  → filtre par filière
  niveau   → filtre par niveau LMD
"""
from django.urls import path

from .api import RapportPDFView, RapportExcelView, RapportCSVView

app_name = "reporting_api"

urlpatterns = [
    path("rapports/pdf/", RapportPDFView.as_view(), name="rapport_pdf"),
    path("rapports/excel/", RapportExcelView.as_view(), name="rapport_excel"),
    path("rapports/csv/", RapportCSVView.as_view(), name="rapport_csv"),
]
