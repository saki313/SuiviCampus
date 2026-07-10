"""Vues API pour les rapports — téléchargement PDF/Excel/CSV via API REST.

Même logique que les vues web (views_rapports) mais accessibles via JWT
pour les consommateurs programmatiques.
"""
from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone

from apps.reporting.services.pdf_export import exporter_pdf
from apps.reporting.services.excel_export import exporter_excel
from apps.reporting.services.csv_export import exporter_csv


class RapportPDFView(APIView):
    """Téléchargement du rapport PDF via API (BF08)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filiere = request.query_params.get("filiere") or None
        niveau = request.query_params.get("niveau") or None
        buffer = exporter_pdf(filiere=filiere, niveau=niveau)
        filename = f"rapport_suivi_academique_{timezone.now():%Y%m%d}.pdf"
        resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


class RapportExcelView(APIView):
    """Téléchargement de l'export Excel via API (BF08)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filiere = request.query_params.get("filiere") or None
        niveau = request.query_params.get("niveau") or None
        buffer = exporter_excel(filiere=filiere, niveau=niveau)
        filename = f"indicateurs_academiques_{timezone.now():%Y%m%d}.xlsx"
        resp = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


class RapportCSVView(APIView):
    """Téléchargement de l'export CSV via API (BF08)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filiere = request.query_params.get("filiere") or None
        niveau = request.query_params.get("niveau") or None
        buffer = exporter_csv(filiere=filiere, niveau=niveau)
        filename = f"indicateurs_academiques_{timezone.now():%Y%m%d}.csv"
        resp = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp
