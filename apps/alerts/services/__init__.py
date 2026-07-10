"""Service Gestionnaire d'Alertes (BF04) — flux DS2 du mémoire.

DS2 : GestionnaireAlertes → ParametreAlerte (seuils) → Alerte →
       notification Etudiant/Responsable → Recommandation → archive.

Déclenché après chaque calcul de score de risque par le moteur KPI.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from apps.alerts.models import Alerte, ParametreAlerte, Recommandation
from apps.accounts.models import ProfilEtudiant
from apps.analytics.models import IndicateurAcademique
from apps.common.enums import NiveauRisque, StatutAlerte, TypeAlerte

logger = logging.getLogger("apps.alerts")


def get_parametres_actifs() -> ParametreAlerte:
    """Récupère les paramètres d'alerte actifs (BF13).

    S'il n'en existe pas, crée les paramètres par défaut (Eq 2.1).
    """
    params = ParametreAlerte.objects.filter(active=True).first()
    if params is None:
        params = ParametreAlerte.objects.create()
    return params


def _message_alerte(etudiant: ProfilEtudiant, type_alerte: str, score: float) -> str:
    """Génère un message d'alerte lisible."""
    msgs = {
        TypeAlerte.RISQUE: (
            f"Score de risque élevé ({score:.1f}/100) pour {etudiant.utilisateur}. "
            "Un accompagnement pédagogique est recommandé."
        ),
        TypeAlerte.ECHEC_UE: (
            f"Échec(s) à une ou plusieurs UE détecté(s) pour "
            f"{etudiant.utilisateur}."
        ),
        TypeAlerte.CREDITS: (
            f"Crédits insuffisants pour {etudiant.utilisateur}. "
            "Risque de retard de diplômation."
        ),
        TypeAlerte.ABSENCE: (
            f"Taux d'absentéisme élevé pour {etudiant.utilisateur}."
        ),
    }
    return msgs.get(type_alerte, f"Alerte académique pour {etudiant.utilisateur}.")


def _recommandation_defaut(classification: str) -> tuple[str, str]:
    """Recommandation pédagogique par défaut selon le niveau de risque."""
    if classification == "Eleve":
        return (
            "Entretien individuel obligatoire avec le responsable pédagogique. "
            "Mise en place d'un plan de soutien (tutorat, rattrapages).",
            "haute",
        )
    if classification == "Modere":
        return (
            "Suivi renforcé recommandé. Proposition de séances de soutien "
            "et point pédagogique mensuel.",
            "moyenne",
        )
    return (
        "Étudiant en bonne trajectoire. Maintenir le suivi régulier.",
        "basse",
    )


def generer_alerte(
    etudiant: ProfilEtudiant,
    type_alerte: str,
    niveau_risque: str,
    score: Optional[float] = None,
) -> Optional[Alerte]:
    """Génère une alerte si elle n'existe pas déjà (active) pour cet étudiant.

    Évite la duplication : une seule alerte active par étudiant/type.
    """
    existe = Alerte.objects.filter(
        etudiant=etudiant, type=type_alerte, statut=StatutAlerte.ACTIVE
    ).exists()
    if existe:
        logger.debug("Alerte %s déjà active pour %s — ignorée", type_alerte, etudiant.matricule)
        return None

    alerte = Alerte.objects.create(
        etudiant=etudiant,
        type=type_alerte,
        niveau_risque=niveau_risque,
        score_risque=score,
        message=_message_alerte(etudiant, type_alerte, score or 0.0),
        statut=StatutAlerte.ACTIVE,
    )

    # Génération de la recommandation associée (DS2)
    description, priorite = _recommandation_defaut(niveau_risque)
    Recommandation.objects.create(
        alerte=alerte, description=description, priorite=priorite
    )

    logger.info(
        "Alerte créée : %s [%s] score=%s pour %s",
        type_alerte, niveau_risque, score, etudiant.matricule,
    )
    return alerte


def verifier_et_generer_alertes(
    etudiant: ProfilEtudiant,
    parametres: Optional[ParametreAlerte] = None,
) -> list[Alerte]:
    """Vérifie les seuils et génère les alertes nécessaires pour un étudiant.

    À appeler après calcul du score de risque.
    """
    params = parametres or get_parametres_actifs()
    alertes_generees: list[Alerte] = []

    try:
        indic = IndicateurAcademique.objects.get(etudiant=etudiant, semestre=None)
    except IndicateurAcademique.DoesNotExist:
        return alertes_generees

    # --- Alerte globale de risque (seuil paramétré) ---
    if indic.score_risque is not None and indic.score_risque > params.seuil_modere:
        niveau = NiveauRisque.ELEVE if indic.score_risque > params.seuil_modere else NiveauRisque.MODERE
        al = generer_alerte(
            etudiant, TypeAlerte.RISQUE, niveau, indic.score_risque
        )
        if al:
            alertes_generees.append(al)

    # --- Alerte échec UE ---
    if indic.ues_echec and indic.ues_total and indic.ues_echec / indic.ues_total > 0.3:
        al = generer_alerte(
            etudiant, TypeAlerte.ECHEC_UE, indic.classification_risque, indic.score_risque
        )
        if al:
            alertes_generees.append(al)

    # --- Alerte crédits insuffisants ---
    if indic.credits_total and indic.credits_acquis:
        taux = indic.credits_acquis / indic.credits_total
        if taux < 0.5:
            al = generer_alerte(
                etudiant, TypeAlerte.CREDITS, indic.classification_risque, indic.score_risque
            )
            if al:
                alertes_generees.append(al)

    # --- Alerte absentéisme ---
    if indic.taux_absenteisme and indic.taux_absenteisme > 30:
        al = generer_alerte(
            etudiant, TypeAlerte.ABSENCE, indic.classification_risque, indic.score_risque
        )
        if al:
            alertes_generees.append(al)

    return alertes_generees


def traiter_alerte(alerte: Alerte, utilisateur) -> None:
    """Marque une alerte comme traitée par un responsable (BF04)."""
    alerte.statut = StatutAlerte.TRAITEE
    alerte.traitee_par = utilisateur
    alerte.date_traitement = timezone.now()
    alerte.save(update_fields=["statut", "traitee_par", "date_traitement", "updated_at"])


def archiver_anciennes_alertes(jours: int = 90) -> int:
    """Archive les alertes traitées de plus de N jours."""
    seuil = timezone.now() - timedelta(days=jours)
    qs = Alerte.objects.filter(
        statut=StatutAlerte.TRAITEE, date_traitement__lt=seuil
    )
    count = qs.count()
    qs.update(statut=StatutAlerte.ARCHIVEE)
    return count


def verifier_promotion(filiere=None, niveau=None) -> int:
    """Vérifie et génère les alertes pour toute une promotion.

    Retourne le nombre total d'alertes générées.
    """
    qs = ProfilEtudiant.objects.all()
    if filiere:
        qs = qs.filter(filiere=filiere)
    if niveau:
        qs = qs.filter(niveau=niveau)

    params = get_parametres_actifs()
    total = 0
    for etudiant in qs:
        total += len(verifier_et_generer_alertes(etudiant, params))
    return total
