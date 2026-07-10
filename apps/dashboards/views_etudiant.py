"""Vues du tableau de bord Étudiant (BF01, BF03, BF04, BF05, BF06, BF07).

Maquette mémoire : score de risque 42/100, crédits 90/120, projection juin 2026,
barre de progression 50%, alertes actives, UE critiques.

Toutes les données proviennent des services (risk/analytics/alerts) ;
aucune logique métier dans les templates.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from apps.accounts.models import ProfilEtudiant
from apps.academics.models import ResultatAcademique, HistoriqueAcademique
from apps.alerts.models import Alerte
from apps.risk.services import get_score_etudiant, get_ue_critiques
from apps.analytics.models import IndicateurAcademique


@login_required
def dashboard_etudiant(request):
    """Tableau de bord principal de l'étudiant connecté."""
    etudiant = getattr(request.user, "_profil_etudiant", None)
    if etudiant is None:
        return render(request, "dashboards/acces_refuse.html", {
            "message": "Votre compte n'est pas associé à un profil étudiant."
        }, status=403)

    # Score de risque + indicateurs (BF02, BF06)
    score_data = get_score_etudiant(etudiant)

    # Récupère l'indicateur persisté pour les champs étendus
    try:
        indic = IndicateurAcademique.objects.get(etudiant=etudiant, semestre=None)
    except IndicateurAcademique.DoesNotExist:
        indic = None

    # Alertes actives de l'étudiant (BF04)
    alertes = Alerte.objects.filter(
        etudiant=etudiant, statut="Active"
    ).order_by("-created_at")[:10]

    # UE critiques (celles où l'étudiant est en échec) — BF05
    resultats = ResultatAcademique.objects.filter(
        etudiant=etudiant, valide=False
    ).select_related("ue", "semestre")

    context = {
        "etudiant": etudiant,
        "score": score_data["score"],
        "niveau_risque": score_data["niveau"],
        "indicateurs": score_data["indicateurs"],
        "indicateur_obj": indic,
        "alertes": alertes,
        "ue_echecs": resultats,
    }
    return render(request, "dashboards/etudiant.html", context)


@login_required
def parcours_etudiant(request):
    """Parcours académique complet de l'étudiant (BF01, BF07)."""
    etudiant = getattr(request.user, "_profil_etudiant", None)
    if etudiant is None:
        return render(request, "dashboards/acces_refuse.html", {
            "message": "Votre compte n'est pas associé à un profil étudiant."
        }, status=403)

    # Tous les résultats par semestre (timeline)
    resultats = ResultatAcademique.objects.filter(
        etudiant=etudiant
    ).select_related("ue", "semestre").order_by("-semestre__annee", "ue__code")

    # Historique consolidé (snapshots)
    historique = HistoriqueAcademique.objects.filter(
        etudiant=etudiant
    ).select_related("semestre").order_by("-semestre__annee")

    context = {
        "etudiant": etudiant,
        "resultats": resultats,
        "historique": historique,
    }
    return render(request, "dashboards/etudiant_parcours.html", context)


@login_required
def alertes_etudiant(request):
    """Toutes les alertes de l'étudiant (BF04)."""
    etudiant = getattr(request.user, "_profil_etudiant", None)
    if etudiant is None:
        return render(request, "dashboards/acces_refuse.html", {
            "message": "Votre compte n'est pas associé à un profil étudiant."
        }, status=403)

    alertes = Alerte.objects.filter(
        etudiant=etudiant
    ).select_related("traitee_par").prefetch_related("recommandations").order_by("-created_at")
    context = {"etudiant": etudiant, "alertes": alertes}
    return render(request, "dashboards/etudiant_alertes.html", context)
