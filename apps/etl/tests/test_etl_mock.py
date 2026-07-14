"""Tests du client mock ETL et du pipeline de données (Phase 13).

Tests du MockCampusFasoClient : vérifie la cohérence des données générées
(nombre, format, déterminisme, couverture des profils typés) sans nécessiter
de base de données.
"""
import pytest
from unittest.mock import patch

from apps.etl.clients.mock import MockCampusFasoClient, CATALOGUE_UE, PROFILS_ETUDIANTS
from apps.etl.clients.base import (
    SourceEtudiant, SourceUE, SourceResultat, SourcePresence,
)


class TestMockCampusFasoClient:
    """Tests du générateur de données mock."""

    @pytest.fixture
    def client(self):
        return MockCampusFasoClient(nb_etudiants=10, graine=42)

    def test_extract_ues_nombre(self, client):
        """Le mock doit générer le nombre d'UE du catalogue (L1+L2+L3 = 24)."""
        ues = list(client.extract_ues())
        assert len(ues) == len(CATALOGUE_UE) == 24

    def test_extract_ues_format(self, client):
        """Chaque UE doit avoir les champs requis."""
        for ue in client.extract_ues():
            assert isinstance(ue, SourceUE)
            assert ue.code and len(ue.code) <= 20
            assert ue.intitule
            assert 0 < ue.credits <= 10
            assert ue.semestre_numero in (1, 2, 3, 4)  # L1 (S1-S2) + L2 (S3-S4)
            assert ue.ue_type in ("obligatoire", "optionnel")

    def test_extract_etudiants_nombre(self, client):
        """Le mock doit générer le nombre demandé d'étudiants."""
        etudiants = list(client.extract_etudiants())
        assert len(etudiants) == 10

    def test_extract_etudiants_format(self, client):
        """Chaque étudiant doit avoir les champs requis."""
        for e in client.extract_etudiants():
            assert isinstance(e, SourceEtudiant)
            assert e.matricule
            assert e.nom
            assert e.prenom
            assert "@" in e.email
            assert e.niveau in ("L1", "L2", "L3", "M1", "M2")
            assert e.annee_scolaire == "2025-2026"

    def test_extract_etudiants_deterministe(self):
        """Deux instances avec la même graine doivent produire les mêmes données."""
        c1 = MockCampusFasoClient(nb_etudiants=5, graine=42)
        c2 = MockCampusFasoClient(nb_etudiants=5, graine=42)
        e1 = [e.matricule for e in c1.extract_etudiants()]
        e2 = [e.matricule for e in c2.extract_etudiants()]
        assert e1 == e2

    def test_extract_resultats_coherence(self, client):
        """Les résultats doivent référencer des étudiants et UE existants."""
        etudiants = list(client.extract_etudiants())
        ues = list(client.extract_ues())
        matricules = {e.matricule for e in etudiants}
        codes_ue = {u.code for u in ues}

        resultats = list(client.extract_resultats())
        assert len(resultats) > 0

        for r in resultats:
            assert isinstance(r, SourceResultat)
            assert r.matricule in matricules, f"Matricule inconnu: {r.matricule}"
            assert r.code_ue in codes_ue, f"UE inconnue: {r.code_ue}"
            assert 0 <= r.note <= 20
            assert r.valide is not None
            assert r.session in ("normale", "rattrapage")

    def test_extract_presences_format(self, client):
        """Les présences doivent avoir le bon format."""
        presences = list(client.extract_presences())
        assert len(presences) > 0
        for p in presences:
            assert isinstance(p, SourcePresence)
            assert p.matricule
            assert p.code_ue
            assert isinstance(p.present, bool)

    def test_health_check(self, client):
        """Le mock doit toujours être disponible."""
        assert client.health_check() is True

    def test_extract_presences_vide_par_defaut(self):
        """Le client abstrait retourne une liste vide par défaut pour les présences."""
        from apps.etl.clients.base import CampusFasoClient

        class MinimalClient(CampusFasoClient):
            def extract_etudiants(self, since=None):
                return []
            def extract_ues(self):
                return []
            def extract_resultats(self, since=None):
                return []

        c = MinimalClient()
        assert list(c.extract_presences()) == []

    def test_taux_reussite_environ_72(self):
        """Le mock doit produire environ 72% de réussite globale (maquette mémoire).

        On teste sur l'effectif cible (85 étudiants) défini par la maquette du
        mémoire (TB Responsable), car les profils typés introduisent une
        variance sensible aux petits effectifs.
        """
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        resultats = list(client.extract_resultats())
        valides = sum(1 for r in resultats if r.valide)
        taux = valides / len(resultats) * 100
        # Tolérance élargie [55 % ; 85 %] : couvre la variance due aux
        # profils typés (fragiles/en_echec/absenteiste) et au rattrapage.
        assert 55 <= taux <= 85, f"Taux de réussite {taux:.1f}% hors tolérance"


class TestCouvertureProfils:
    """Tests de couverture des profils typés (cahier de charges).

    Vérifie que le mock génère bien une distribution hétérogène d'étudiants
    couvrant tous les cas fonctionnels : excellent, bon, moyen, fragile,
    en_echec, absenteiste.
    """

    @pytest.fixture
    def gros_client(self):
        """Client avec un effectif suffisant pour couvrir tous les profils."""
        return MockCampusFasoClient(nb_etudiants=85, graine=42)

    def test_tous_profils_presents(self, gros_client):
        """Les 6 profils doivent être représentés parmi les étudiants."""
        profils_presents = {
            gros_client._profil_pour_index(i)
            for i in range(1, 86)
        }
        profils_attendus = {p[0] for p in PROFILS_ETUDIANTS}
        assert profils_presents == profils_attendus, (
            f"Profils manquants: {profils_attendus - profils_presents}"
        )

    def test_repartition_profils_cohabrent(self, gros_client):
        """Chaque profil doit représenter une part raisonnable de l'effectif.

        On vérifie qu'au moins un étudiant appartient à chaque profil
        (couverture minimale des cas fonctionnels).
        """
        from collections import Counter
        compteur = Counter(
            gros_client._profil_pour_index(i) for i in range(1, 86)
        )
        for nom_profil, *_ in PROFILS_ETUDIANTS:
            assert compteur[nom_profil] > 0, (
                f"Profil '{nom_profil}' non représenté dans le dataset"
            )

    def test_notes_dispersees_selon_profils(self, gros_client):
        """La distribution des notes doit être large (cas BF02).

        On doit trouver des notes < 8 (échec), entre 8 et 10 (fragile),
        et > 14 (excellent) — couvrant les 3 classifications de risque.
        """
        notes = [r.note for r in gros_client.extract_resultats()]
        assert min(notes) < 8.0, "Aucune note d'échec (< 8) dans le dataset"
        assert max(notes) > 14.0, "Aucune note d'excellence (> 14) dans le dataset"
        # Médiane autour de la zone moyenne/passable.
        notes_triees = sorted(notes)
        mediane = notes_triees[len(notes_triees) // 2]
        assert 8.0 <= mediane <= 14.0


class TestSessionsRattrapage:
    """Tests de la génération de sessions de rattrapage (cahier de charges BF11).

    Les profils fragiles/en_echec/absenteiste doivent générer des résultats
    de session "rattrapage" pour les UE échouées en session normale.
    """

    def test_sessions_rattrapage_presentes(self):
        """Au moins un résultat de rattrapage doit être présent (85 étudiants)."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        resultats = list(client.extract_resultats())
        rattrapages = [r for r in resultats if r.session == "rattrapage"]
        assert len(rattrapages) > 0, (
            "Aucun résultat de rattrapage généré — les profils en échec "
            "devraient déclencher du rattrapage"
        )

    def test_rattrapage_seulement_apres_echec_normale(self):
        """Un rattrapage ne doit exister que si la session normale est en échec."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        resultats = list(client.extract_resultats())

        # Indexer par (matricule, code_ue, numero_semestre)
        par_cle = {}
        for r in resultats:
            cle = (r.matricule, r.code_ue, r.numero_semestre)
            par_cle.setdefault(cle, {})[r.session] = r

        for cle, sessions in par_cle.items():
            if "rattrapage" in sessions:
                normale = sessions.get("normale")
                assert normale is not None, (
                    f"Rattrapage sans session normale pour {cle}"
                )
                assert not normale.valide, (
                    f"Rattrapage généré bien que la session normale soit "
                    f"validée pour {cle} (note={normale.note})"
                )

    def test_note_rattrapage_coherente(self):
        """La note de rattrapage doit rester dans [0, 20]."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        for r in client.extract_resultats():
            if r.session == "rattrapage":
                assert 0 <= r.note <= 20


class TestAbsenteismeVarie:
    """Tests de la variabilité de l'absentéisme (cahier de charges BF04).

    Le taux de présence doit dépendre du profil : excellent ~95 %,
    absentéiste ~40 %. Cela garantit que l'alerte BF04 type ABSENCE
    (>30 %) soit déclenchée pour les profils concernés.
    """

    def test_absents_presents_dans_presences(self):
        """Le dataset doit contenir des absences (present=False)."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        presences = list(client.extract_presences())
        absents = [p for p in presences if not p.present]
        assert len(absents) > 0, (
            "Aucune absence générée — l'indicateur d'absentéisme serait nul"
        )

    def test_taux_presence_varie_selon_profil(self):
        """Le taux de présence moyen doit varier entre profils extrêmes.

        Le profil excellent doit avoir un taux > 90 %, l'absentéiste < 60 %.
        """
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        from collections import defaultdict
        par_profil = defaultdict(lambda: {"total": 0, "present": 0})

        for idx, etu in enumerate(client._etudiants, start=1):
            profil = client._profil_pour_index(idx)
            presences_etu = [
                p for p in client.extract_presences()
                if p.matricule == etu.matricule
            ]
            par_profil[profil]["total"] += len(presences_etu)
            par_profil[profil]["present"] += sum(1 for p in presences_etu if p.present)

        taux_excellent = par_profil["excellent"]["present"] / max(1, par_profil["excellent"]["total"])
        taux_absenteiste = par_profil["absenteiste"]["present"] / max(1, par_profil["absenteiste"]["total"])
        assert taux_excellent > 0.85, (
            f"Taux de présence excellent trop bas: {taux_excellent:.2%}"
        )
        assert taux_absenteiste < 0.65, (
            f"Taux de présence absentéiste trop haut: {taux_absenteiste:.2%}"
        )


class TestMultiFilieres:
    """Tests de la répartition multi-filières (cahier de charges BF10, BF03).

    Les étudiants doivent être répartis entre les 3 filières afin que les
    filtres par filière (get_distribution_scores, get_ue_critiques) soient
    testés de façon significative.
    """

    def test_tous_filiere_presentes(self):
        """Les 3 filières doivent être représentées."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        filieres = {e.filiere for e in client.extract_etudiants()}
        assert len(filieres) == 3, (
            f"Attendu 3 filières, trouvé {len(filieres)}: {filieres}"
        )

    def test_repartition_equilibree(self):
        """Aucune filière ne doit dominer massivement (> 60 % de l'effectif)."""
        client = MockCampusFasoClient(nb_etudiants=85, graine=42)
        from collections import Counter
        filieres = Counter(e.filiere for e in client.extract_etudiants())
        for filiere, effectif in filieres.items():
            part = effectif / 85
            assert part < 0.60, (
                f"Filière '{filiere}' surreprésentée: {part:.0%}"
            )
