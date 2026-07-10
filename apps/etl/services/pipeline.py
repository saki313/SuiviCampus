"""Pipeline ETL — Extract → Transform → Load (DS3, BF11).

Mémoire §3.2.2 :
  - Extraction différentielle (depuis le dernier checkpoint)
  - Transformation selon les règles métier (validation, normalisation)
  - Chargement dans le Data Warehouse (OLTP + tables Dim/Fait)
  - Historisation (EtlRun + logs)
  - Gestion erreurs + reprise après échec

Le pipeline déclenche ensuite le recalcul KPI + alertes (Phase 10).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_tz
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.etl.clients import get_client, CampusFasoClient
from apps.etl.models import EtlRun, EtlCheckpoint, EtlExecutionErreur
from apps.accounts.models import Utilisateur, ProfilEtudiant
from apps.academics.models import (
    UniteEnseignement, Semestre, ResultatAcademique, Presence, ParcoursAcademique,
)
from apps.warehouse.models import (
    DimEtudiant, DimUE, DimSemestre, DimTemps, FaitResultats,
)

logger = logging.getLogger("apps.etl")


class EtlPipeline:
    """Orchestrateur du pipeline ETL complet."""

    def __init__(self, client: Optional[CampusFasoClient] = None, run: Optional[EtlRun] = None):
        self.client = client or get_client()
        self.run = run
        self._checkpoints = {}

    # ----------------------------------------------------------------------
    # Point d'entrée principal
    # ----------------------------------------------------------------------
    def executer(self, differentiel: bool = True) -> EtlRun:
        """Exécute un cycle ETL complet.

        Args:
            differentiel: si True, n'extrait que les modifications depuis le
                          dernier checkpoint (mémoire §3.2.2).
        """
        self.run = EtlRun.objects.create(
            source_mode=getattr(self.client, "source_mode", "mock"),
            statut=EtlRun.Statut.EN_COURS,
        )
        self.run.ajouter_log(f"[START] Pipeline ETL démarré (mode={self.run.source_mode})")

        try:
            # Étape 1 — Extraction + transformation + chargement OLTP
            self._charger_ues()
            self._charger_etudiants(differentiel)
            self._charger_resultats(differentiel)
            self._charger_presences(differentiel)

            # Étape 2 — Chargement du Data Warehouse (schéma étoile)
            self._charger_data_warehouse()

            # Succès
            self.run.statut = EtlRun.Statut.SUCCES
            self.run.date_fin = timezone.now()
            self.run.ajouter_log(
                f"[OK] Pipeline terminé : {self.run.nb_etudiants_charges} étudiants, "
                f"{self.run.nb_resultats_charges} résultats, {self.run.nb_ue_charges} UE."
            )
            # Mise à jour des checkpoints
            if differentiel:
                self._mettre_a_jour_checkpoints()

        except Exception as e:
            self.run.statut = EtlRun.Statut.ECHEC
            self.run.date_fin = timezone.now()
            self.run.nb_erreurs += 1
            self.run.ajouter_log(f"[ERREUR] {e}")
            EtlExecutionErreur.objects.create(
                run=self.run, etape="pipeline", message=str(e)
            )
            logger.exception("Échec du pipeline ETL")
            raise
        finally:
            self.run.save()

        return self.run

    # ----------------------------------------------------------------------
    # Chargement OLTP
    # ----------------------------------------------------------------------
    def _charger_ues(self) -> None:
        """Charge le catalogue des UE (idempotent, upsert)."""
        count = 0
        for source_ue in self.client.extract_ues():
            try:
                UniteEnseignement.objects.update_or_create(
                    code=source_ue.code,
                    defaults={
                        "intitule": source_ue.intitule,
                        "credits": source_ue.credits,
                        "semestre_numero": source_ue.semestre_numero,
                        "ue_type": source_ue.ue_type,
                    },
                )
                count += 1
            except Exception as e:
                self._log_erreur("load_ue", f"UE {source_ue.code}", e)
        self.run.nb_ue_extraits = count
        self.run.nb_ue_charges = count
        self.run.ajouter_log(f"[UE] {count} unités d'enseignement chargées.")

    def _charger_etudiants(self, differentiel: bool) -> None:
        """Charge les étudiants (crée utilisateur + profil + parcours)."""
        since = self._get_since("etudiants") if differentiel else None
        count = 0
        for src in self.client.extract_etudiants(since):
            try:
                with transaction.atomic():
                    # Utilisateur (upsert par email)
                    user, created = Utilisateur.objects.get_or_create(
                        email=src.email,
                        defaults={
                            "username": src.matricule,
                            "first_name": src.prenom,
                            "last_name": src.nom,
                            "role": "etudiant",
                        },
                    )
                    if not created:
                        user.first_name = src.prenom
                        user.last_name = src.nom
                        user.role = "etudiant"
                        user.save()

                    # Profil étudiant (upsert par matricule)
                    profil, _ = ProfilEtudiant.objects.update_or_create(
                        matricule=src.matricule,
                        defaults={
                            "utilisateur": user,
                            "niveau": src.niveau,
                            "filiere": src.filiere,
                            "promotion": src.promotion,
                            "annee_scolaire": src.annee_scolaire,
                        },
                    )

                    # Parcours académique (un par année)
                    ParcoursAcademique.objects.get_or_create(
                        etudiant=profil,
                        annee_scolaire=src.annee_scolaire,
                        defaults={
                            "filiere": src.filiere,
                            "niveau": src.niveau,
                            "statut": "en_cours",
                        },
                    )
                    count += 1
            except Exception as e:
                self._log_erreur("load_etudiant", src.matricule, e)
        self.run.nb_etudiants_extraits = count
        self.run.nb_etudiants_charges = count
        self.run.ajouter_log(f"[ETU] {count} étudiants chargés.")

    def _charger_resultats(self, differentiel: bool) -> None:
        """Charge les résultats académiques (upsert par contrainte unique)."""
        since = self._get_since("resultats") if differentiel else None
        count = 0
        # Cache des UE et Semestres pour éviter les requêtes répétées
        ue_cache = {ue.code: ue for ue in UniteEnseignement.objects.all()}
        sem_cache = {}

        for src in self.client.extract_resultats(since):
            try:
                ue = ue_cache.get(src.code_ue)
                if ue is None:
                    self._log_erreur("load_resultat", src.code_ue, f"UE {src.code_ue} introuvable")
                    continue

                # Semestre (cache par (numero, annee))
                key = (src.numero_semestre, src.annee_semestre)
                sem = sem_cache.get(key)
                if sem is None:
                    sem, _ = Semestre.objects.get_or_create(
                        numero=src.numero_semestre,
                        annee=src.annee_semestre,
                        defaults={
                            "annee_scolaire": src.annee_scolaire,
                        },
                    )
                    sem_cache[key] = sem

                etudiant = ProfilEtudiant.objects.filter(matricule=src.matricule).first()
                if etudiant is None:
                    self._log_erreur("load_resultat", src.matricule, f"Étudiant {src.matricule} introuvable")
                    continue

                ResultatAcademique.objects.update_or_create(
                    etudiant=etudiant, ue=ue, semestre=sem, session=src.session,
                    defaults={
                        "note": src.note,
                        "credits": src.credits,
                        "valide": src.valide,
                        "date_evaluation": src.date_evaluation,
                    },
                )
                count += 1
            except Exception as e:
                self._log_erreur("load_resultat", f"{src.matricule}/{src.code_ue}", e)
        self.run.nb_resultats_extraits = count
        self.run.nb_resultats_charges = count
        self.run.ajouter_log(f"[RES] {count} résultats chargés.")

    def _charger_presences(self, differentiel: bool) -> None:
        """Charge les présences (indicateur A, D5)."""
        since = self._get_since("presences") if differentiel else None
        count = 0
        ue_cache = {ue.code: ue for ue in UniteEnseignement.objects.all()}
        etu_cache = {e.matricule: e for e in ProfilEtudiant.objects.all()}

        for src in self.client.extract_presences(since):
            try:
                ue = ue_cache.get(src.code_ue)
                etudiant = etu_cache.get(src.matricule)
                if not ue or not etudiant:
                    continue
                Presence.objects.update_or_create(
                    etudiant=etudiant, ue=ue, date_cours=src.date_cours,
                    defaults={"present": src.present},
                )
                count += 1
            except Exception as e:
                self._log_erreur("load_presence", f"{src.matricule}/{src.code_ue}", e)
        self.run.nb_presences_extraites = count
        self.run.ajouter_log(f"[PRES] {count} présences chargées.")

    # ----------------------------------------------------------------------
    # Chargement Data Warehouse (schéma en étoile)
    # ----------------------------------------------------------------------
    def _charger_data_warehouse(self) -> None:
        """Alimente les tables Dim_* et Fait_Resultats depuis l'OLTP.

        Le DW est la couche analytique : on le (re)construit à partir des
        données OLTP fraîchement chargées.
        """
        # Dim_Etudiant
        for profil in ProfilEtudiant.objects.all():
            DimEtudiant.objects.update_or_create(
                source_id=profil.id,
                defaults={
                    "matricule": profil.matricule,
                    "niveau_actuel": profil.niveau,
                    "filiere": profil.filiere,
                    "promotion": profil.promotion,
                    "annee_scolaire": profil.annee_scolaire,
                },
            )
        # Dim_UE
        for ue in UniteEnseignement.objects.all():
            DimUE.objects.update_or_create(
                source_id=ue.id,
                defaults={
                    "code": ue.code,
                    "intitule": ue.intitule,
                    "credits": ue.credits,
                    "semestre": ue.semestre_numero,
                },
            )
        # Dim_Semestre
        for sem in Semestre.objects.all():
            DimSemestre.objects.update_or_create(
                source_id=sem.id,
                defaults={
                    "numero": sem.numero,
                    "annee": sem.annee,
                    "date_debut": sem.date_debut,
                    "date_fin": sem.date_fin,
                },
            )
        # Fait_Resultats (table centrale)
        dim_etu = {d.source_id: d for d in DimEtudiant.objects.all()}
        dim_ue = {d.source_id: d for d in DimUE.objects.all()}
        dim_sem = {d.source_id: d for d in DimSemestre.objects.all()}

        for res in ResultatAcademique.objects.select_related("etudiant", "ue", "semestre").all():
            de = dim_etu.get(res.etudiant_id)
            due = dim_ue.get(res.ue_id)
            ds = dim_sem.get(res.semestre_id)
            if not (de and due and ds):
                continue
            # Dim_Temps (basée sur l'année du semestre + session)
            temps, _ = DimTemps.objects.get_or_create(
                annee=res.semestre.annee,
                session_examen=res.session,
                annee_scolaire=res.semestre.annee_scolaire,
            )
            FaitResultats.objects.update_or_create(
                etudiant=de, ue=due, semestre=ds, temps=temps,
                defaults={
                    "note": res.note,
                    "credits": res.credits,
                    "valide": res.valide,
                    "score_risque": None,  # calculé par le moteur KPI (Phase 10)
                },
            )
        self.run.ajouter_log("[DW] Data Warehouse alimenté.")

    # ----------------------------------------------------------------------
    # Synchronisation différentielle + reprise
    # ----------------------------------------------------------------------
    def _get_since(self, ressource: str) -> Optional[str]:
        """Récupère le timestamp du dernier checkpoint pour la ressource."""
        cp = EtlCheckpoint.objects.filter(ressource=ressource).first()
        if cp and cp.derniere_synchro:
            return cp.derniere_synchro.isoformat()
        return None

    def _mettre_a_jour_checkpoints(self) -> None:
        """Met à jour les checkpoints après un run réussi."""
        maintenant = timezone.now()
        for ressource in ("etudiants", "resultats", "presences"):
            cp, _ = EtlCheckpoint.objects.get_or_create(ressource=ressource)
            cp.derniere_synchro = maintenant
            cp.nb_total_synchro += getattr(
                self.run,
                f"nb_{ressource}_extraits" if ressource != "presences" else "nb_presences_extraites",
                0,
            )
            cp.save()

    # ----------------------------------------------------------------------
    # Gestion des erreurs
    # ----------------------------------------------------------------------
    def _log_erreur(self, etape: str, ressource: str, erreur) -> None:
        """Journalise une erreur sans interrompre le pipeline (reprise)."""
        msg = str(erreur)
        self.run.nb_erreurs += 1
        self.run.ajouter_log(f"[ERR] {etape} {ressource}: {msg}")
        EtlExecutionErreur.objects.create(
            run=self.run, etape=etape, ressource=ressource, message=msg
        )
        if self.run.nb_erreurs > 100:
            raise RuntimeError("Trop d'erreurs ETL (>100) — abandon.")


def executer_etl(differentiel: bool = True) -> EtlRun:
    """Point d'entrée fonctionnel : exécute un cycle ETL."""
    pipeline = EtlPipeline()
    return pipeline.executer(differentiel=differentiel)
