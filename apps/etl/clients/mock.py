"""Mock de service.campusfaso.bf — données réalistes pour démo et tests.

Reproduit fidèlement les chiffres des maquettes du mémoire :
  - ~85 étudiants (maquette TB Responsable : "effectif 85 étudiants")
  - taux de réussite ~72% (maquette TB Responsable)
  - ~12 étudiants à risque élevé (maquette TB Responsable)
  - scores de risque répartis (maquette TB Étudiant : score 42/100)
  - 90/120 crédits (maquette TB Étudiant)

Génération déterministe (graine fixe) pour des tests reproductibles.
"""
from __future__ import annotations

import random
from typing import Iterable

from .base import (
    CampusFasoClient, SourceEtudiant, SourceUE, SourceResultat, SourcePresence,
)


# Catalogue UE — 12 UE réparties sur les niveaux LMD (filière Informatique).
# Crédits ECTS conformes au système LMD (30 crédits / semestre).
CATALOGUE_UE = [
    # Semestre 1 (L1)
    ("INF101", "Algorithmique et structures de données", 6, 1, "obligatoire"),
    ("INF102", "Introduction à la programmation", 6, 1, "obligatoire"),
    ("MAT101", "Mathématiques discrètes", 6, 1, "obligatoire"),
    ("ANG101", "Anglais technique", 3, 1, "obligatoire"),
    ("METH101", "Méthodologie du travail universitaire", 3, 1, "obligatoire"),
    ("WEB101", "Bases du web (HTML/CSS/JS)", 6, 1, "obligatoire"),
    # Semestre 2 (L1)
    ("INF201", "Programmation orientée objet", 6, 2, "obligatoire"),
    ("INF202", "Bases de données relationnelles", 6, 2, "obligatoire"),
    ("MAT201", "Probabilités et statistiques", 6, 2, "obligatoire"),
    ("RES201", "Réseaux informatiques", 6, 2, "obligatoire"),
    ("ANG201", "Anglais technique II", 3, 2, "obligatoire"),
    ("PROJ201", "Projet tutoré", 3, 2, "obligatoire"),
]

FILIERES = [
    ("Informatique", "INF"),
    ("Mathématiques", "MAT"),
    ("Génie Logiciel", "GL"),
]

NIVEAUX = ["L1", "L2", "L3", "M1", "M2"]
ANNEE_SCOLAIRE = "2025-2026"


class MockCampusFasoClient(CampusFasoClient):
    """Source de données simulée pour le développement.

    Génère un dataset réaliste de manière déterministe.
    """

    def __init__(self, nb_etudiants: int = 85, graine: int = 42):
        self.nb_etudiants = nb_etudiants
        self.graine = graine
        self._rng = random.Random(graine)
        # Pré-générer la liste des étudiants une seule fois (déterministe).
        # Cela garantit que extract_resultats/extraction_presences
        # référencent les MÊMES étudiants que extract_etudiants.
        self._etudiants = list(self._generer_etudiants())

    # -- Extraction des UE (catalogue figé) ---------------------------------
    def extract_ues(self) -> Iterable[SourceUE]:
        for code, intitule, credits, sem, ue_type in CATALOGUE_UE:
            yield SourceUE(
                code=code, intitule=intitule, credits=credits,
                semestre_numero=sem, ue_type=ue_type,
            )

    # -- Générateur interne des étudiants (appelé une seule fois) ------------
    def _generer_etudiants(self) -> Iterable[SourceEtudiant]:
        for i in range(1, self.nb_etudiants + 1):
            filiere_nom, prefixe = self._rng.choice(FILIERES)
            niveau = self._rng.choice(NIVEAUX)
            matricule = f"{prefixe}{i:04d}"
            # Distribution des noms/prénoms réalistes (Burkina Faso)
            noms = ["OUEDRAOGO", "SAWADOGO", "KABORE", "TRAORE", "COMPAORE",
                    "ZONGO", "SANOU", "ILBOUDO", "NACOULMA", "OUATTARA",
                    "TAPSOBA", "BONKOUNGOU", "BAMOGO", "YAMEOGO"]
            prenoms = ["Moussa", "Awa", "Ibrahim", "Fatimata", "Adama", "Aïcha",
                       "Issouf", "Mariam", "Boukary", "Rasmané", "Aminata",
                       "Salif", "Kadiatou", "Jean-Marc"]
            nom = self._rng.choice(noms)
            prenom = self._rng.choice(prenoms)
            email = f"{prenom.lower()}.{nom.lower()}{i}@campusfaso.bf"
            yield SourceEtudiant(
                matricule=matricule, nom=nom, prenom=prenom, email=email,
                niveau=niveau, filiere=filiere_nom,
                promotion=f"{self._rng.choice([2023, 2024, 2025])}-{self._rng.choice([2026, 2027, 2028])}",
                annee_scolaire=ANNEE_SCOLAIRE,
            )

    def extract_etudiants(self, since: str | None = None) -> Iterable[SourceEtudiant]:
        """Retourne la liste pré-générée (déterministe, cohérente avec resultats)."""
        return iter(self._etudiants)

    # -- Extraction des résultats (réalistes, ~72% de réussite) --------------
    def extract_resultats(self, since: str | None = None) -> Iterable[SourceResultat]:
        annee = 2025
        # Utilise la liste pré-générée (même RNG que extract_etudiants)
        for etu in self._etudiants:
            # Niveau → numéro de semestre académique (L1=1, L2=3, L3=5, M1=7, M2=9)
            base_sem = NIVEAUX.index(etu.niveau) * 2 + 1
            for offset in (0, 1):  # 2 semestres de l'année
                num_sem = base_sem + offset
                # UE du semestre (les 6 du semestre 1 ou 2 du catalogue L1)
                semestre_catal = (offset % 2) + 1
                for code, intitule, credits, sem, ue_type in CATALOGUE_UE:
                    if sem != semestre_catal:
                        continue
                    # ~72% de réussite globale (maquette mémoire)
                    # Notes distribuées : moyenne ~11,5/20
                    note = self._note_realiste()
                    valide = note >= 10.0
                    yield SourceResultat(
                        matricule=etu.matricule,
                        code_ue=code,
                        numero_semestre=num_sem,
                        annee_semestre=annee,
                        annee_scolaire=ANNEE_SCOLAIRE,
                        note=note,
                        credits=credits if valide else 0,
                        valide=valide,
                        session="normale",
                        date_evaluation=f"{annee}-{6 + offset * 6:02d}-15",
                    )

    def extract_presences(self, since: str | None = None) -> Iterable[SourcePresence]:
        """[D5] Génère des présences réalistes pour l'indicateur d'absentéisme."""
        for etu in self._etudiants:
            for code, _, _, sem, _ in CATALOGUE_UE[:6]:  # UE du S1
                # ~85% de présence moyenne
                for jour in range(1, 11):
                    present = self._rng.random() < 0.85
                    yield SourcePresence(
                        matricule=etu.matricule, code_ue=code,
                        date_cours=f"2025-{(sem * 2) % 12 or 12:02d}-{jour:02d}",
                        present=present,
                    )

    def _note_realiste(self) -> float:
        """Génère une note réaliste : ~72% de réussite, moyenne ~11,5/20.

        Distribution : 30% bon (13-18), 42% moyen-passage (10-13),
                       18% fragile (8-10), 10% échec (< 8).
        """
        tirage = self._rng.random()
        if tirage < 0.30:
            return round(self._rng.uniform(13, 18), 2)
        elif tirage < 0.72:
            return round(self._rng.uniform(10, 13), 2)
        elif tirage < 0.90:
            return round(self._rng.uniform(8, 10), 2)
        else:
            return round(self._rng.uniform(4, 8), 2)
