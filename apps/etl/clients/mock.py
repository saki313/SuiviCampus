"""Mock de service.campusfaso.bf — données réalistes pour démo et tests.

Reproduit fidèlement les chiffres des maquettes du mémoire :
  - ~85 étudiants (maquette TB Responsable : "effectif 85 étudiants")
  - taux de réussite ~72% (maquette TB Responsable)
  - ~12 étudiants à risque élevé (maquette TB Responsable)
  - scores de risque répartis (maquette TB Étudiant : score 42/100)
  - 90/120 crédits (maquette TB Étudiant)

Génération déterministe (graine fixe) pour des tests reproductibles.

Profils académiques typés (6) : excellent, bon, moyen, fragile, en_echec,
absenteiste. Chaque profil pilote la distribution des notes, le taux de
réussite et le taux de présence, afin de garantir la couverture de TOUS les
cas fonctionnels du cahier de charges :
  - BF02 : scores répartis sur les 3 classifications (Faible/Modéré/Élevé)
  - BF04 : les 4 types d'alertes (RISQUE, ECHEC_UE, CREDITS, ABSENCE)
  - BF06 : progression variée (de ~0 % à ~95 %)
  - BF10 : UE avec taux d'échec différenciés
  - BF11 : pipeline ETL testé sur données hétérogènes
"""
from __future__ import annotations

import random
from typing import Iterable

from .base import (
    CampusFasoClient, SourceEtudiant, SourceUE, SourceResultat, SourcePresence,
)


# Catalogue UE — 24 UE réparties sur 6 semestres LMD (L1, L2, L3).
# Crédits ECTS conformes au système LMD (30 crédits / semestre).
# On couvre L1 à L3 afin que les étudiants de chaque niveau reçoivent des
# résultats cohérents avec leur niveau (et non mappés sur L1 uniquement).
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
    # Semestre 3 (L2)
    ("INF301", "Algorithmique avancée", 6, 3, "obligatoire"),
    ("INF302", "Systèmes d'exploitation", 6, 3, "obligatoire"),
    ("MAT301", "Algèbre linéaire", 6, 3, "obligatoire"),
    ("ARCH301", "Architecture des ordinateurs", 6, 3, "obligatoire"),
    ("ANG301", "Anglais technique III", 3, 3, "obligatoire"),
    ("PROJ301", "Projet logiciel", 3, 3, "obligatoire"),
    # Semestre 4 (L2)
    ("INF401", "Intelligence artificielle", 6, 4, "obligatoire"),
    ("INF402", "Développement web avancé", 6, 4, "obligatoire"),
    ("MAT401", "Recherche opérationnelle", 6, 4, "obligatoire"),
    ("SEC401", "Sécurité informatique", 6, 4, "obligatoire"),
    ("ANG401", "Anglais technique IV", 3, 4, "obligatoire"),
    ("STAGE401", "Stage professionnel", 3, 4, "obligatoire"),
]

FILIERES = [
    ("Informatique", "INF"),
    ("Mathématiques", "MAT"),
    ("Génie Logiciel", "GL"),
]

NIVEAUX = ["L1", "L2", "L3", "M1", "M2"]
ANNEE_SCOLAIRE = "2025-2026"

# Profils académiques typés — pilotes de la distribution des notes, du taux
# de réussite et du taux de présence. La part (poids) de chaque profil est
# choisie pour qu'à 85 étudiants la moyenne pondérée du taux de réussite
# reste ~72 % (maquette mémoire) :
#   0,15·0,95 + 0,30·0,85 + 0,25·0,70 + 0,15·0,40 + 0,10·0,15 + 0,05·0,50
#   ≈ 0,70 — cohérent avec la marge d'acceptation [60 % ; 85 %].
PROFILS_ETUDIANTS = [
    # (nom, part, note_min, note_max, taux_presence, genère du rattrapage ?)
    ("excellent",   0.15, 14.0, 18.0, 0.95, False),
    ("bon",         0.30, 10.5, 15.0, 0.90, False),
    ("moyen",       0.25,  9.0, 13.0, 0.85, False),
    ("fragile",     0.15,  7.0, 11.0, 0.75, True),
    ("en_echec",    0.10,  4.0,  9.0, 0.65, True),
    ("absenteiste", 0.05,  6.0, 11.0, 0.40, True),
]


class MockCampusFasoClient(CampusFasoClient):
    """Source de données simulée pour le développement.

    Génère un dataset réaliste de manière déterministe, en assignant chaque
    étudiant à un profil académique typé (excellent → absentéiste) afin de
    couvrir tous les cas fonctionnels du cahier de charges.
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
        # Distribution des noms/prénoms réalistes (Burkina Faso)
        noms = ["OUEDRAOGO", "SAWADOGO", "KABORE", "TRAORE", "COMPAORE",
                "ZONGO", "SANOU", "ILBOUDO", "NACOULMA", "OUATTARA",
                "TAPSOBA", "BONKOUNGOU", "BAMOGO", "YAMEOGO"]
        prenoms = ["Moussa", "Awa", "Ibrahim", "Fatimata", "Adama", "Aïcha",
                   "Issouf", "Mariam", "Boukary", "Rasmané", "Aminata",
                   "Salif", "Kadiatou", "Jean-Marc"]
        # Profils et filières répartis de façon déterministe pour garantir
        # la couverture de tous les cas, même avec peu d'étudiants.
        for i in range(1, self.nb_etudiants + 1):
            profil = self._profil_pour_index(i)
            filiere_nom, prefixe = FILIERES[(i - 1) % len(FILIERES)]
            # Niveau déterministe : on privilégie L1/L2/L3 (catalogue UE).
            # Les cycles M1/M2 sont rares mais présents (coverage).
            niveau = NIVEAUX[(i - 1) % 3]  # L1, L2, L3 rotatifs
            if i % 11 == 0:  # ~1 étudiant sur 11 en Master
                niveau = "M1"
            matricule = f"{prefixe}{i:04d}"
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
        for idx, etu in enumerate(self._etudiants, start=1):
            profil = self._profil_pour_index(idx)
            # Niveau → numéro de semestre académique (L1=1, L2=3, L3=5, M1=7, M2=9)
            base_sem = NIVEAUX.index(etu.niveau) * 2 + 1
            for offset in (0, 1):  # 2 semestres de l'année
                num_sem = base_sem + offset
                # On ne génère des résultats que pour les semestres présents
                # au catalogue (1 à 6 = L1 à L3). Au-delà (M1/M2), on retombe
                # sur le catalogue du semestre correspondant modulo 6.
                semestre_catal = ((num_sem - 1) % 6) + 1
                for code, intitule, credits, sem, ue_type in CATALOGUE_UE:
                    if sem != semestre_catal:
                        continue
                    # ~72% de réussite globale (maquette mémoire), modulé par
                    # le profil de l'étudiant.
                    note = self._note_realiste(profil)
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
                    # Rattrapage pour les profils fragiles/en_echec/absenteiste
                    # dont la note est insuffisante en session normale.
                    if profil in ("fragile", "en_echec", "absenteiste") and not valide:
                        note_rat = self._note_rattrapage(note, profil)
                        # Mois de rattrapage : septembre (S1) / mars (S2).
                        # On reste dans [1; 12] via modulo 12.
                        mois_rat = ((9 + offset * 6 - 1) % 12) + 1
                        yield SourceResultat(
                            matricule=etu.matricule,
                            code_ue=code,
                            numero_semestre=num_sem,
                            annee_semestre=annee,
                            annee_scolaire=ANNEE_SCOLAIRE,
                            note=note_rat,
                            credits=credits if note_rat >= 10.0 else 0,
                            valide=note_rat >= 10.0,
                            session="rattrapage",
                            date_evaluation=f"{annee}-{mois_rat:02d}-15",
                        )

    def extract_presences(self, since: str | None = None) -> Iterable[SourcePresence]:
        """[D5] Génère des présences réalistes pour l'indicateur d'absentéisme.

        Le taux de présence dépend du profil de l'étudiant (de 95 % pour un
        excellent à 40 % pour un absentéiste), ce qui déclenche l'alerte BF04
        de type ABSENCE (>30 %) pour les profils à fort absentéisme.
        """
        for idx, etu in enumerate(self._etudiants, start=1):
            profil = self._profil_pour_index(idx)
            taux_presence = self._taux_presence(profil)
            for code, _, _, sem, _ in CATALOGUE_UE[:6]:  # UE du S1
                for jour in range(1, 11):
                    present = self._rng.random() < taux_presence
                    yield SourcePresence(
                        matricule=etu.matricule, code_ue=code,
                        date_cours=f"2025-{(sem * 2) % 12 or 12:02d}-{jour:02d}",
                        present=present,
                    )

    # -- Aides à la génération déterministe par profil ----------------------
    # Table de répartition déterministe pré-calculée sur 100 places : chaque
    # profil occupe un nombre de places proportionnel à sa part (arrondi), et
    # les places sont entrelacées (round-robin stratifié) pour garantir que
    # tous les profils apparaissent même avec un faible effectif.
    _TABLE_PROFILS_100 = None  # construite paresseusement (cf. _construire_table)

    @classmethod
    def _construire_table(cls) -> tuple[str, ...]:
        """Construit la table de 100 profils entrelacés.

        On répartit d'abord chaque profil sur ses places consécutives, puis on
        entrelace les profils (interleave) pour éviter qu'un petit effectif ne
        tombe uniquement sur les premiers profils. Ainsi avec 10 étudiants on
        obtient déjà une bonne diversité.
        """
        places_par_profil = []
        cumul = 0
        reste = 100
        for i, (nom, part, *_) in enumerate(PROFILS_ETUDIANTS):
            if i == len(PROFILS_ETUDIANTS) - 1:
                nb = reste  # le dernier absorbe l'arrondi
            else:
                nb = round(part * 100)
                reste -= nb
            places_par_profil.append([nom] * nb)
        # Entrelacement stratifié : on prend un élément de chaque profil à tour
        # de rôle, ce qui disperse les profils rares au lieu de les concentrer
        # en fin de table.
        table = []
        taille_max = max(len(p) for p in places_par_profil)
        for position in range(taille_max):
            for paquet in places_par_profil:
                if position < len(paquet):
                    table.append(paquet[position])
        # Sécurité : on complète à 100 si l'arrondi a laissé des trous.
        while len(table) < 100:
            table.append(PROFILS_ETUDIANTS[-1][0])
        return tuple(table[:100])

    def _profil_pour_index(self, index: int) -> str:
        """Assigne un profil déterministe à un étudiant (index 1-based).

        La table de 100 profils entrelacés garantit la présence de tous les
        profils même avec un faible effectif (contrairement à une distribution
        cumulative classique).
        """
        if self._TABLE_PROFILS_100 is None:
            self._TABLE_PROFILS_100 = self._construire_table()
        return self._TABLE_PROFILS_100[(index - 1) % 100]

    def _note_realiste(self, profil: str) -> float:
        """Génère une note réaliste selon le profil de l'étudiant.

        Chaque profil a son intervalle de notes (cf. PROFILS_ETUDIANTS),
        ce qui produit une distribution hétérogène couvrant tous les cas :
        excellents (14-18), bons (11-15), moyens (10-13), fragiles (7-11),
        en_echec (4-9), absentéistes (6-11).
        """
        for nom, _, note_min, note_max, _, _ in PROFILS_ETUDIANTS:
            if nom == profil:
                return round(self._rng.uniform(note_min, note_max), 2)
        # Fallback : distribution historique (~11,5/20).
        return round(self._rng.uniform(8, 15), 2)

    def _note_rattrapage(self, note_normale: float, profil: str) -> float:
        """Génère une note de rattrapage (généralement améliorée).

        En pratique, la majorité des étudiants rattrapent leur UE en session
        de rattrapage ; seuls les profils en_echec échouent souvent. On vise
        un taux de réussite ~70 % au rattrapage (cohérent avec la maquette).
        """
        # Tirage déterministe : 70 % de réussite globale au rattrapage.
        if self._rng.random() < 0.70:
            # Réussite : note ramenée juste au-dessus de 10.
            note_rat = self._rng.uniform(10.0, min(15.0, note_normale + 5.0))
        else:
            # Échec : note voisine de la note normale (légère remontée).
            note_rat = self._rng.uniform(max(0.0, note_normale - 1.0), 9.5)
        # Les profils en_echec ont plus de mal à rattraper.
        if profil == "en_echec" and self._rng.random() < 0.5:
            note_rat = self._rng.uniform(5.0, 9.5)
        return round(min(20.0, max(0.0, note_rat)), 2)

    def _taux_presence(self, profil: str) -> float:
        """Taux de présence selon le profil (absenteiste ~40 % → excellent ~95 %)."""
        for nom, _, _, _, taux, _ in PROFILS_ETUDIANTS:
            if nom == profil:
                return taux
        return 0.85
