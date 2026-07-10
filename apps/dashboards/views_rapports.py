"""Vues de téléchargement des rapports (BF08) — couche présentation.

Ces vues délèguent la génération aux services reporting et renvoient
les fichiers en tant que pièces jointes téléchargeables.

Aucune logique métier ici : les services font tout le travail.
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone

from apps.reporting.services.pdf_export import exporter_pdf
from apps.reporting.services.excel_export import exporter_excel
from apps.reporting.services.csv_export import exporter_csv


@login_required
def telecharger_pdf(request):
    """Génère et télécharge le rapport PDF (BF08)."""
    filiere = request.GET.get("filiere", "").strip() or None
    niveau = request.GET.get("niveau", "").strip() or None

    try:
        buffer = exporter_pdf(filiere=filiere, niveau=niveau)
    except Exception as e:
        return HttpResponseNotFound(f"Erreur de génération PDF : {e}")

    filename = f"rapport_suivi_academique_{timezone.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def telecharger_excel(request):
    """Génère et télécharge l'export Excel (BF08)."""
    filiere = request.GET.get("filiere", "").strip() or None
    niveau = request.GET.get("niveau", "").strip() or None

    try:
        buffer = exporter_excel(filiere=filiere, niveau=niveau)
    except Exception as e:
        return HttpResponseNotFound(f"Erreur de génération Excel : {e}")

    filename = f"indicateurs_academiques_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def telecharger_csv(request):
    """Génère et télécharge l'export CSV (BF08)."""
    filiere = request.GET.get("filiere", "").strip() or None
    niveau = request.GET.get("niveau", "").strip() or None

    try:
        buffer = exporter_csv(filiere=filiere, niveau=niveau)
    except Exception as e:
        return HttpResponseNotFound(f"Erreur de génération CSV : {e}")

    filename = f"indicateurs_academiques_{timezone.now().strftime('%Y%m%d')}.csv"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
