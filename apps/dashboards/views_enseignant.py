"""Vues du tableau de bord Enseignant / Responsable (BF03, BF07, BF09, BF10).

Maquette TB Responsable : effectif 85, taux de réussite 72%, 12 étudiants
à risque élevé, distribution des scores, alertes récentes.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Prefetch
from django.shortcuts import render

from apps.accounts.models import ProfilEtudiant, ResponsablePedagogique
from apps.academics.models import ResultatAcademique
from apps.analytics.models import IndicateurAcademique
from apps.alerts.models import Alerte
from apps.risk.services import get_distribution_scores, get_ue_critiques


def _taux_reussite(filiere=None, niveau=None) -> float:
    """Calcule le taux de réussite d'une promotion en UNE seule requête agrégée.

    Évite le double comptage `.filter(valide=True).count() / .count()`
    qui générait 2 requêtes distinctes (problème N+1 des dashboards).
    """
    qs = ResultatAcademique.objects.all()
    if filiere:
        qs = qs.filter(etudiant__filiere=filiere)
    if niveau:
        qs = qs.filter(etudiant__niveau=niveau)
    agg = qs.aggregate(
        total=Count("id"),
        valides=Count("id", filter=Q(valide=True)),
    )
    return (100.0 * agg["valides"] / agg["total"]) if agg["total"] else 0.0


@login_required
def dashboard_enseignant(request):
    """Tableau de bord enseignant : étudiants suivis + statistiques (BF03)."""
    # Un enseignant voit les étudiants de ses départements/filières (simplifié : tous)
    etudiants = ProfilEtudiant.objects.select_related("utilisateur").all()

    # Statistiques agrégées (1 requête via aggregate au lieu de 2)
    total = etudiants.count()
    taux_reussite = _taux_reussite()

    # Distribution des risques (1 requête agrégée dans le service)
    distribution = get_distribution_scores()

    # UE critiques (BF10) — agrégation SQL dans le service
    ue_critiques = get_ue_critiques(limite=5)

    # Étudiants à risque élevé (1 requête COUNT plutôt qu'un SELECT *)
    nb_risque_eleve = IndicateurAcademique.objects.filter(
        classification_risque="Eleve", semestre=None
    ).count()

    context = {
        "total_etudiants": total,
        "taux_reussite": round(taux_reussite, 1),
        "distribution": distribution,
        "ue_critiques": ue_critiques,
        "etudiants_risque_eleve": nb_risque_eleve,
    }
    return render(request, "dashboards/enseignant.html", context)


@login_required
def liste_etudiants(request):
    """Liste des étudiants (DataTable) — BF01, BF07.

    Optimisation (Phase 15) : les indicateurs sont récupérés via
    prefetch_related (1 seule requête SQL supplémentaire) au lieu d'être
    chargés intégralement en mémoire dans un dict. DataTables gère la
    pagination côté client ; le serveur reste léger via select_related.
    """
    etudiants = (
        ProfilEtudiant.objects
        .select_related("utilisateur")
        .prefetch_related(
            # On ne précharge QUE l'indicateur global (semestre=None)
            Prefetch(
                "indicateurs",
                queryset=IndicateurAcademique.objects.filter(semestre=None),
                to_attr="indicateur_global",
            )
        )
        .all()
    )
    # On garde l'interface (etudiant, indicateur) attendue par le template
    # sans instancier tout le dict indicateurs en mémoire.
    context = {
        "etudiants": [
            (e, e.indicateur_global[0] if e.indicateur_global else None)
            for e in etudiants
        ],
    }
    return render(request, "dashboards/etudiants_liste.html", context)


@login_required
def dashboard_responsable(request):
    """Tableau de bord de pilotage du responsable (BF03, BF09, BF10).

    Maquette : KPI promotion, distribution des scores, alertes récentes.
    """
    user = request.user
    # Filtres par filière/niveau gérés (si responsable a un profil)
    filiere_filter = None
    niveau_filter = None
    try:
        resp = ResponsablePedagogique.objects.get(enseignant__utilisateur=user)
        filiere_filter = resp.filiere_geree or None
        niveau_filter = resp.niveau_gere or None
    except ResponsablePedagogique.DoesNotExist:
        pass

    # Effectif et KPI promotion
    etudiants_qs = ProfilEtudiant.objects.all()
    if filiere_filter:
        etudiants_qs = etudiants_qs.filter(filiere=filiere_filter)
    if niveau_filter:
        etudiants_qs = etudiants_qs.filter(niveau=niveau_filter)
    total = etudiants_qs.count()

    # Distribution des scores (agrégation SQL dans le service)
    distribution = get_distribution_scores(filiere_filter, niveau_filter)

    # Taux de réussite global (1 requête agrégée au lieu de 2)
    taux_reussite = _taux_reussite(filiere_filter, niveau_filter)

    # Alertes récentes (toute la promotion)
    alertes_recentes = Alerte.objects.filter(
        statut="Active"
    ).select_related("etudiant__utilisateur").order_by("-created_at")[:8]

    # UE critiques
    ue_critiques = get_ue_critiques(filiere_filter, niveau_filter, limite=10)

    # Redoublements / réorientations (BF09) : étudiants avec statut abandon
    redoublements = ProfilEtudiant.objects.filter(
        parcours__statut="abandon"
    ).distinct().count()

    context = {
        "user": user,
        "filiere": filiere_filter,
        "niveau": niveau_filter,
        "total_etudiants": total,
        "taux_reussite": round(taux_reussite, 1),
        "distribution": distribution,
        "alertes_recentes": alertes_recentes,
        "ue_critiques": ue_critiques,
        "nb_redoublements": redoublements,
        "nb_risque_eleve": distribution.get("Eleve", 0),
    }
    return render(request, "dashboards/responsable.html", context)


@login_required
def rapports_view(request):
    """Page d'accès aux rapports (BF08) — redirige vers le module reporting."""
    return render(request, "dashboards/rapports.html")
