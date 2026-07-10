"""Adaptateur abstrait pour service.campusfaso.bf (DS3, D4).

L'ETL ne lit JAMAIS en écriture sur campusfaso.bf — stricte lecture seule.
Cette interface abstraite permet de brancher :
  - un mock (MockCampusFasoClient) pour le développement/démo
  - une vraie API REST lecture-seule (ApiCampusFasoClient) en production

[DEDUCTION D4] : campusfaso.bf n'expose pas d'API documentée dans le mémoire.
Le mock reproduit fidèlement les données attendues ; l'implémentation réelle
se branchera sans modifier l'ETL.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass
class SourceEtudiant:
    """Snapshot d'un étudiant tel que fourni par campusfaso.bf."""
    matricule: str
    nom: str
    prenom: str
    email: str
    niveau: str        # L1..M2
    filiere: str
    promotion: str
    annee_scolaire: str


@dataclass
class SourceUE:
    """Une UE du catalogue source."""
    code: str
    intitule: str
    credits: int
    semestre_numero: int
    ue_type: str       # "obligatoire" | "optionnel"


@dataclass
class SourceResultat:
    """Résultat d'un étudiant dans une UE à un semestre (source brute)."""
    matricule: str
    code_ue: str
    numero_semestre: int
    annee_semestre: int
    annee_scolaire: str
    note: float
    credits: int
    valide: bool
    session: str       # "normale" | "rattrapage"
    date_evaluation: str | None = None


@dataclass
class SourcePresence:
    """[D5] Présence d'un étudiant à une séance — quand la source le permet."""
    matricule: str
    code_ue: str
    date_cours: str
    present: bool


class CampusFasoClient(ABC):
    """Interface de lecture des données académiques (lecture seule stricte)."""

    @abstractmethod
    def extract_etudiants(self, since: str | None = None) -> Iterable[SourceEtudiant]:
        """Extrait les étudiants. `since` (ISO) pour synchro différentielle."""

    @abstractmethod
    def extract_ues(self) -> Iterable[SourceUE]:
        """Extrait le catalogue des UE."""

    @abstractmethod
    def extract_resultats(self, since: str | None = None) -> Iterable[SourceResultat]:
        """Extrait les résultats. `since` pour synchro différentielle."""

    def extract_presences(self, since: str | None = None) -> Iterable[SourcePresence]:
        """Extrait les présences. Optionnel — défaut : vide (D5)."""
        return []

    def health_check(self) -> bool:
        """Vérifie la disponibilité de la source."""
        return True
