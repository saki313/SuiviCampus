"""Export PDF — Synthèse académique (BF08).

Génère un rapport PDF mis en page contenant :
  - Page de garde (titre, date, filtres)
  - Synthèse globale (effectif, taux de réussite, distribution des risques)
  - Tableau des indicateurs par étudiant
  - Tableau des UE critiques

Utilise ReportLab (génération côté serveur, sans dépendance LaTeX).
"""
from __future__ import annotations

import io
from datetime import date
from typing import Optional

from django.db.models import Count, Avg, Q
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

from apps.accounts.models import ProfilEtudiant
from apps.academics.models import ResultatAcademique
from apps.analytics.models import IndicateurAcademique

# Palette de couleurs (cohérente avec le CSS : --c-primary, --c-faible, etc.)
_C_PRIMARY = colors.HexColor("#2b6cb0")
_C_SUCCESS = colors.HexColor("#2f855a")
_C_WARNING = colors.HexColor("#d69e2e")
_C_DANGER = colors.HexColor("#c53030")
_C_LIGHT = colors.HexColor("#f7fafc")
_C_DARK = colors.HexColor("#1a202c")
_C_GRAY = colors.HexColor("#718096")
_C_HEADER_BG = colors.HexColor("#2b6cb0")
_C_ROW_ALT = colors.HexColor("#edf2f7")


def _build_styles():
    """Construit les styles de paragraphes pour le rapport."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="RapportTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=_C_PRIMARY,
        spaceAfter=6,
        alignment=1,  # centré
    ))
    styles.add(ParagraphStyle(
        name="RapportSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=_C_GRAY,
        alignment=1,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=_C_PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=9,
        textColor=_C_GRAY,
    ))
    styles.add(ParagraphStyle(
        name="KPIValue",
        parent=styles["Normal"],
        fontSize=20,
        textColor=_C_PRIMARY,
        alignment=1,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="KPILabel",
        parent=styles["Normal"],
        fontSize=9,
        textColor=_C_GRAY,
        alignment=1,
        spaceAfter=4,
    ))
    return styles


def exporter_pdf(
    filiere: Optional[str] = None,
    niveau: Optional[str] = None,
    titre_rapport: Optional[str] = None,
) -> io.BytesIO:
    """Génère un rapport PDF de synthèse académique.

    Args:
        filiere: filtre par filière (None = toutes).
        niveau: filtre par niveau LMD (None = tous).
        titre_rapport: titre personnalisé (sinon auto-généré).

    Returns:
        BytesIO contenant le PDF.
    """
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Rapport de Suivi Académique",
        author="Plateforme de Suivi Académique",
    )

    styles = _build_styles()
    elements = []

    # --- Page de garde ---
    elements.append(Spacer(1, 4 * cm))
    elements.append(Paragraph(
        "Plateforme Décisionnelle<br/>de Suivi Académique",
        styles["RapportTitle"],
    ))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(
        "Rapport de synthèse académique",
        styles["RapportSubtitle"],
    ))
    elements.append(Spacer(1, 1 * cm))

    now = timezone.now()
    filtre_txt = "Toutes"
    if filiere:
        filtre_txt = filiere
    if niveau:
        filtre_txt += f" — {niveau}"

    info_data = [
        ["Date de génération", now.strftime("%d/%m/%Y à %H:%M")],
        ["Filtres", filtre_txt],
        ["Source", "service.campusfaso.bf (lecture seule)"],
    ]
    info_table = Table(info_data, colWidths=[5 * cm, 10 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), _C_DARK),
        ("TEXTCOLOR", (1, 0), (1, -1), _C_GRAY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # --- Synthèse globale ---
    elements.append(Paragraph(
        "1. Synthèse globale de la promotion",
        styles["SectionTitle"],
    ))

    indicateurs_qs = _queryset_indicateurs(filiere, niveau)
    total_etudiants = indicateurs_qs.count()

    # Distribution des risques
    distribution = indicateurs_qs.values("classification_risque").annotate(
        effectif=Count("id")
    )
    dist_dict = {"Faible": 0, "Modere": 0, "Eleve": 0}
    for row in distribution:
        key = row["classification_risque"]
        if key in dist_dict:
            dist_dict[key] = row["effectif"]

    # Taux de réussite global
    resultats_qs = ResultatAcademique.objects.all()
    if filiere:
        resultats_qs = resultats_qs.filter(etudiant__filiere=filiere)
    if niveau:
        resultats_qs = resultats_qs.filter(etudiant__niveau=niveau)
    total_res = resultats_qs.count()
    res_valides = resultats_qs.filter(valide=True).count()
    taux_reussite = (100.0 * res_valides / total_res) if total_res else 0

    # KPI en tableau
    kpi_data = [
        [
            Paragraph("<b>Effectif</b>", styles["KPILabel"]),
            Paragraph(f"<b>{total_etudiants}</b>", styles["KPIValue"]),
            Paragraph("<b>Taux réussite</b>", styles["KPILabel"]),
            Paragraph(f"<b>{taux_reussite:.1f} %</b>", styles["KPIValue"]),
        ],
        [
            Paragraph("Risque faible", styles["KPILabel"]),
            Paragraph(f"<b>{dist_dict['Faible']}</b>", ParagraphStyle("g", parent=styles["KPIValue"], textColor=_C_SUCCESS)),
            Paragraph("Risque élevé", styles["KPILabel"]),
            Paragraph(f"<b>{dist_dict['Eleve']}</b>", ParagraphStyle("r", parent=styles["KPIValue"], textColor=_C_DANGER)),
        ],
        [
            Paragraph("Risque modéré", styles["KPILabel"]),
            Paragraph(f"<b>{dist_dict['Modere']}</b>", ParagraphStyle("y", parent=styles["KPIValue"], textColor=_C_WARNING)),
            Paragraph("Résultats validés", styles["KPILabel"]),
            Paragraph(f"<b>{res_valides}/{total_res}</b>", styles["KPIValue"]),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, _C_PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 1 * cm))

    # --- Tableau des indicateurs par étudiant ---
    elements.append(Paragraph(
        "2. Indicateurs par étudiant",
        styles["SectionTitle"],
    ))

    etu_headers = [
        "Matricule", "Nom", "Niv.", "Score",
        "Classif.", "Prog. %", "Crédits",
        "UE échec", "Absent. %",
    ]
    etu_data = [etu_headers]

    for indic in indicateurs_qs[:200]:  # Limite pour la taille du PDF
        etu = indic.etudiant
        user = etu.utilisateur
        etu_data.append([
            etu.matricule,
            user.get_full_name() or user.username,
            etu.niveau,
            _fmt_score(indic.score_risque),
            indic.classification_risque or "—",
            _fmt(indic.taux_progression, "%"),
            f"{indic.credits_acquis}/{indic.credits_total}",
            f"{indic.ues_echec}/{indic.ues_total}",
            _fmt(indic.taux_absenteisme, "%"),
        ])

    col_widths = [2.3 * cm, 3.2 * cm, 1.2 * cm, 1.5 * cm,
                  1.5 * cm, 1.5 * cm, 1.8 * cm, 1.5 * cm, 1.5 * cm]
    etu_table = Table(etu_data, colWidths=col_widths, repeatRows=1)
    etu_table_style = [
        # En-tête
        ("BACKGROUND", (0, 0), (-1, 0), _C_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, _C_PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
    ]
    # Lignes alternées
    for i in range(1, len(etu_data)):
        if i % 2 == 0:
            etu_table_style.append(("BACKGROUND", (0, i), (-1, i), _C_ROW_ALT))
    etu_table.setStyle(TableStyle(etu_table_style))
    elements.append(etu_table)
    elements.append(PageBreak())

    # --- UE critiques ---
    elements.append(Paragraph(
        "3. Unités d'Enseignement sous surveillance (BF10)",
        styles["SectionTitle"],
    ))

    ue_stats = (
        ResultatAcademique.objects.values("ue__code", "ue__intitule", "ue__credits")
        .annotate(
            total=Count("id"),
            echecs=Count("id", filter=Q(valide=False)),
            moyenne=Avg("note"),
        )
        .order_by("-echecs")[:15]
    )
    ue_headers = ["Code", "Intitulé", "Effectif", "Échecs", "Taux échec", "Moy."]
    ue_data = [ue_headers]
    for row in ue_stats:
        total = row["total"]
        echecs = row["echecs"]
        taux = (echecs / total * 100) if total else 0
        ue_data.append([
            row["ue__code"],
            (row["ue__intitule"] or "")[:40],
            str(total),
            str(echecs),
            f"{taux:.1f} %",
            f"{row['moyenne']:.1f}" if row["moyenne"] else "—",
        ])

    ue_col_widths = [1.8 * cm, 5.5 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm]
    ue_table = Table(ue_data, colWidths=ue_col_widths, repeatRows=1)
    ue_style = [
        ("BACKGROUND", (0, 0), (-1, 0), _C_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, _C_PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
    ]
    for i in range(1, len(ue_data)):
        if i % 2 == 0:
            ue_style.append(("BACKGROUND", (0, i), (-1, i), _C_ROW_ALT))
    ue_table.setStyle(TableStyle(ue_style))
    elements.append(ue_table)

    # --- Pied de page ---
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_C_GRAY))
    elements.append(Paragraph(
        "Plateforme décisionnelle de suivi académique — complémentaire à "
        "<code>service.campusfaso.bf</code> (lecture seule).<br/>"
        "Document généré automatiquement — " + now.strftime("%d/%m/%Y %H:%M"),
        styles["SmallText"],
    ))

    doc.build(elements)
    output.seek(0)
    return output


def _queryset_indicateurs(filiere=None, niveau=None):
    """QuerySet filtré des indicateurs globaux (semestre=None)."""
    qs = IndicateurAcademique.objects.filter(
        semestre=None
    ).select_related("etudiant", "etudiant__utilisateur").order_by(
        "-score_risque"
    )
    if filiere:
        qs = qs.filter(etudiant__filiere=filiere)
    if niveau:
        qs = qs.filter(etudiant__niveau=niveau)
    return qs


def _fmt(valeur, suffixe="") -> str:
    """Formate une valeur numérique."""
    if valeur is None:
        return "—"
    return f"{valeur:.1f}{suffixe}"


def _fmt_score(score) -> str:
    """Formate un score de risque avec couleur indicative."""
    if score is None:
        return "—"
    return f"{score:.0f}/100"
