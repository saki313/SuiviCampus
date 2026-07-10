"""Vues du tableau de bord Administrateur (BF11, BF12, BF13).

Console admin : ETL, utilisateurs, paramètres d'alerte, audit.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from apps.accounts.models import Utilisateur
from apps.alerts.models import ParametreAlerte
from apps.audit.models import AuditLog
from apps.etl.models import EtlRun


@login_required
def admin_etl(request):
    """Supervision ETL (BF11) — historique des runs + déclenchement."""
    runs = EtlRun.objects.all()[:20]
    dernier_run = runs.first()
    context = {
        "runs": runs,
        "dernier_run": dernier_run,
    }
    return render(request, "dashboards/admin_etl.html", context)


@login_required
def admin_utilisateurs(request):
    """Gestion des utilisateurs (BF12)."""
    utilisateurs = (
        Utilisateur.objects
        .select_related("_profil_etudiant", "_profil_enseignant", "_profil_administrateur")
        .all()
    )
    context = {"utilisateurs": utilisateurs}
    return render(request, "dashboards/admin_utilisateurs.html", context)


@login_required
def admin_parametres(request):
    """Paramétrage des seuils d'alerte (BF13)."""
    params = ParametreAlerte.objects.filter(active=True).first()
    if params is None:
        params = ParametreAlerte.objects.create()

    if request.method == "POST":
        params.seuil_faible = float(request.POST.get("seuil_faible", 30))
        params.seuil_modere = float(request.POST.get("seuil_modere", 60))
        params.ponderation_notes = float(request.POST.get("pond_notes", 0.40))
        params.ponderation_credits = float(request.POST.get("pond_credits", 0.30))
        params.ponderation_ue_echec = float(request.POST.get("pond_ue", 0.20))
        params.ponderation_absenteisme = float(request.POST.get("pond_abs", 0.10))
        params.save()
        messages.success(request, "Paramètres d'alerte mis à jour.")
        return redirect("dashboards:admin_parametres")

    context = {"params": params}
    return render(request, "dashboards/admin_parametres.html", context)


@login_required
def admin_audit(request):
    """Journal d'audit (sécurité).

    Optimisation (Phase 15) : on filtre via l'index idx_audit_user_time
    et on limite à 100 entrées (déjà présent) — aucune jointure nécessaire
    car les champs sont dénormalisés (utilisateur stocké en texte).
    """
    logs = AuditLog.objects.all()[:100]
    context = {"logs": logs}
    return render(request, "dashboards/admin_audit.html", context)
