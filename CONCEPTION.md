# DOCUMENT DE CONCEPTION INTERNE

> Plateforme Décisionnelle de Suivi Académique et d'Analyse des Parcours Étudiants
> Plateforme **complémentaire** à `service.campusfaso.bf` (lecture seule sur ses données).

Ce document est le livrable des **Phases 1 à 4** (analyse → modèle métier → architecture → arborescence).
Il est dérivé exclusivement du mémoire (`Docs/rapport_suivi_academique-chap2-full.pdf`), du MCD/diagramme de classes, des 3 diagrammes de séquence et du diagramme de cas d'utilisation. Les points non définis explicitement sont déduits et signalés par **[DÉDUCTION]**.

---

## 1. SYNTHÈSE DU DOMAINE (Phase 1)

### 1.1 Vision métier
La plateforme existante `service.campusfaso.bf` est **purement administrative** (inscriptions, notes, bulletins). Elle ne fournit **aucune** capacité analytique : pas de vision longitudinale du parcours, pas d'alertes, pas d'indicateurs, pas d'aide à la décision pédagogique.

La plateforme à construire est un **entrepôt de données décisionnel** qui :
1. **lit** les données de `service.campusfaso.bf` (jamais n'écrit dessus, jamais ne le modifie) ;
2. les **transforme et historise** dans un Data Warehouse PostgreSQL (schéma en étoile) ;
3. **calcule** des indicateurs (KPI) et un **score de risque** composite pour chaque étudiant ;
4. **détecte** les situations à risque et **génère des alertes** automatiques ;
5. **projette** la diplomation et la progression ;
6. **expose** le tout via API REST + interface web profilée par acteur.

### 1.2 Acteurs (issus du diagramme de cas d'utilisation)

| Acteur | Type | Rôle |
|--------|------|------|
| **Étudiant** | interne | Consulte son parcours, sa progression, ses indicateurs, reçoit ses alertes |
| **Enseignant** | interne | Accède aux infos/stats des étudiants qu'il suit, identifie les UE difficiles |
| **Responsable pédagogique** | interne | Hérite de Enseignant. Tableaux de bord de pilotage, rapports, gestion redoublements/réorientations |
| **Administrateur** | interne | Gère utilisateurs, rôles, ETL, paramètres, audit, logs |
| **service.campusfaso.bf** | externe | **Source de données** — fournit notes, inscriptions, volumes horaires via ETL |

**Hiérarchie d'héritage** (du diagramme de classes) :
```
Utilisateur (abstract)
├── Étudiant
├── Enseignant
│   └── ResponsablePédagogique   ← un responsable EST un enseignant + responsabilités
└── Administrateur
```

### 1.3 Cahier des charges (synthèse)

**13 besoins fonctionnels (BF)** :

| ID | Besoin | Acteurs | Priorité |
|----|--------|---------|----------|
| BF01 | Consulter le parcours académique complet | Étudiant, Enseignant | Haute |
| BF02 | Calculer un score de risque académique | Système | Haute |
| BF03 | Afficher un tableau de bord personnalisé | Tous | Haute |
| BF04 | Générer et notifier des alertes | Système, Responsable | Haute |
| BF05 | Suivre la validation des UE et crédits LMD | Étudiant, Responsable | Haute |
| BF06 | Estimer la progression vers le diplôme | Étudiant, Responsable | Haute |
| BF07 | Consulter l'historique académique consolidé | Étudiant, Enseignant | Haute |
| BF08 | Générer rapports et statistiques | Responsable, Admin | Moyenne |
| BF09 | Analyser redoublements et réorientations | Responsable, Admin | Moyenne |
| BF10 | Identifier les UE les plus difficiles | Enseignant, Responsable | Moyenne |
| BF11 | Synchroniser les données avec campusfaso.bf | Système | Haute |
| BF12 | Gérer utilisateurs et rôles | Administrateur | Haute |
| BF13 | Paramétrer les seuils et règles d'alerte | Administrateur | Moyenne |

**Relations `«include»`** (du diagramme UC) : `Recevoir alertes (BF04)` et `Générer rapports (BF08)` **incluent** tous deux `Consulter score de risque (BF02)` — BF02 est le traitement analytique central. Le calcul effectif est **interne** (scheduler) ; les acteurs ne font que consulter son résultat.

**8 besoins non fonctionnels** : Confidentialité, Contrôle d'accès, Disponibilité, Sauvegarde, Performance (< 3 s), Ergonomie, Interopérabilité, Évolutivité (ISO/IEC 25010).

**Contraintes** : lecture seule sur campusfaso.bf, open source privilégié, ~5000 étudiants.

---

## 2. MODÈLE MÉTIER (Phase 2)

### 2.1 Classes métier (du diagramme de classes — 16 classes)

**Classes acteurs (5)** : `Utilisateur` (abstraite), `Étudiant`, `Enseignant`, `ResponsablePédagogique`, `Administrateur`.

**Classes métier (11)** : `ParcoursAcadémique`, `RésultatAcadémique`, `UnitéEnseignement`, `Semestre`, `HistoriqueAcadémique`, `IndicateurAcadémique`, `Alerte`, `ParamètreAlerte`, `Recommandation`, `TableauDeBord`, `Rapport`.

**Compositions** (cycle de vie dépendant du conteneur, ♦) :
- `ParcoursAcadémique` ♦→ `RésultatAcadémique`
- `TableauDeBord` ♦→ `IndicateurAcadémique`

**Attributs dérivés** (notation `/`) : les indicateurs calculés de `IndicateurAcadémique`.

### 2.2 Schéma dimensionnel du Data Warehouse (schéma en étoile, Fig 2.8)

Table de faits centrale **`Fait_Résultats`** + 4 dimensions :

```
                    Dim_Etudiant                Dim_UE
                    idEtudiant (PK)             idUE (PK)
                    matricule                   code
                    niveauActuel                intitule
                    filiere                     credits
                    promotion                   semestre

Fait_Résultats
   idEtudiant (FK) ──┘                           └── idUE (FK)
   idUE (FK)
   idSemestre (FK) ──┐
   idTemps (FK) ──┐  │
                  │  │   Dim_Semestre
                  │  └── idSemestre (PK)
                  │      numero
                  │      annee
                  │      dateDebut
                  │      dateFin
                  │
                  └── Dim_Temps
                      idTemps (PK)
                      annee / mois / sessionExamen / anneeScolaire

   note: Decimal
   credits: Integer
   valide: Boolean
   scoreRisque: Float
```

### 2.3 Formules KPI formalisées (à respecter EXACTEMENT)

**Équation 2.1 — Score de risque** (composante centrale, BF02) :
```
ScoreRisque = 0,40 × N + 0,30 × C + 0,20 × U + 0,10 × A
```
où :
- **N** = `(1 − m̄/20) × 100`  — indicateur notes (m̄ = moyenne générale)
- **C** = `(1 − c_acq / c_total) × 100`  — indicateur crédits
- **U** = `(u_echec / u_total) × 100`  — proportion d'UE en échec
- **A** = `(1 − s_pres / s_tot) × 100`  — taux d'absentéisme

**Preuve de bornage** : chaque indicateur ∈ [0;100], Σcoeff = 1 ⇒ ScoreRisque ∈ [0;100].
**Classification** : Faible ≤ 30, Modéré 31–60, Élevé > 60.

**Équation 2.2 — Progression & diplomation** (BF06) :
```
TauxProgression = (c_acq / c_total) × 100  [%]
SemestresRestants = (c_total − c_acq) / c̄_sem     (c̄_sem = moyenne crédits validés/semestre)
```
La moyenne `c̄_sem` est **l'historique réel** de l'étudiant (pas un idéal théorique).

### 2.4 Flux critiques (3 diagrammes de séquence)

**DS1 — Calcul du score de risque** (déclenché par scheduler nocturne post-ETL) :
```
Scheduler → KPI/MoteurScoreRisque → DataWarehouse (lecture données) →
calcul N, C, U, A → ScoreRisque → persister dans Fait_Résultats / Indicateur →
si score > seuil → déclencher GestionnaireAlertes
```

**DS2 — Génération d'une alerte** :
```
GestionnaireAlertes → lire ParamètreAlerte (seuils) → créer Alerte →
notifier Étudiant/Responsable → créer Recommandation → archiver
```

**DS3 — Synchronisation ETL** :
```
Scheduler → ETL → Extraction différentielle campusfaso.bf →
Transformation (règles métier) → Chargement DW → Historisation →
déclencher recalcul KPI/ScoreRisque → logs + reprise sur échec
```

---

## 3. ARCHITECTURE LOGICIELLE (Phase 3)

### 3.1 Décision sur Metabase / Airflow

Le mémoire recommande **Metabase** (dashboards no-code) et **Apache Airflow** (orchestration ETL).
Le cahier des charges impose **Bootstrap + Charts.js + DataTables** pour le frontend et **Cron** pour le scheduler.

→ **Décision [DÉDUCTION]** : Le mémoire liste Metabase comme *recommandation* de conception, mais le cahier des charges opérationnel (le prompt) **impose** une interface web maison (Bootstrap/Charts.js/DataTables) et Cron. On privilégie le cahier des charges opérationnel : on construit **les dashboards en Django + Charts.js** (et non Metabase) afin de livrer une application autonome et unifiable. De même, on utilise **Django Management Commands + Cron** (et non Airflow, explicitement jugé « surdimensionné » §2.3 du mémoire pour ~5000 étudiants). Le `README-2.md` documentera l'option Metabase/Airflow comme alternative.

### 3.2 Architecture en couches (Clean Architecture)

Respect strict de la séparation imposée par le cahier des charges — **aucune logique métier dans les vues ou les serializers** :

```
┌─────────────────────────────────────────────────────────────┐
│  presentation  │ Templates HTML, vues Django, JS (Charts.js) │  → ce que voit l'utilisateur
├─────────────────────────────────────────────────────────────┤
│  api           │ DRF ViewSets, Serializers, URLs, Swagger     │  → sérialisation / HTTP uniquement
├─────────────────────────────────────────────────────────────┤
│  application   │ Use cases : orchestration ETL, recalcul KPI  │  → orchestration des services
├─────────────────────────────────────────────────────────────┤
│  domain        │ Entités, règles KPI (formules 2.1/2.2),      │  → LE MÉTIER PUR (testable, sans Django)
│                │ calculs ScoreRisque, seuils, projections     │
├─────────────────────────────────────────────────────────────┤
│  analytics     │ Moteur KPI, agrégations OLAP                 │
├─────────────────────────────────────────────────────────────┤
│  etl           │ Extract / Transform / Load différentiel      │
├─────────────────────────────────────────────────────────────┤
│  reporting     │ Génération PDF / Excel / CSV                 │
├─────────────────────────────────────────────────────────────┤
│  security      │ JWT, RBAC, permissions, audit                │
├─────────────────────────────────────────────────────────────┤
│  infrastructure│ Models Django/ORM, adapteurs campusfaso.bf   │  → accès données (PostgreSQL/DW)
├─────────────────────────────────────────────────────────────┤
│  common        │ Mixins, enums, helpers, exceptions           │
└─────────────────────────────────────────────────────────────┘
```

**Règle d'or des dépendances** : `domain` ne dépend de rien (Django inclus) — il contient les formules pures. `infrastructure` implémente les interfaces du `domain`. Les `services` (couche `application`) orchestrent.

### 3.3 Déploiement cible (3 nœuds, diagramme de déploiement du mémoire)

```
[Client navigateur] ──HTTP/HTTPS──> [Serveur applicatif Django + Gunicorn]
                                              │
                                              └──TCP/5432──> [Serveur BD/Data Warehouse PostgreSQL]
                                                                    │
                                                                    └── (ETL lecture seule) ──> service.campusfaso.bf
```

### 3.4 Stack technique retenue

| Couche | Technologie |
|--------|-------------|
| Backend | Django 5.x + Django REST Framework |
| Domaine (formules) | Python pur (testable hors Django) |
| BD / DW | PostgreSQL 16 (schéma en étoile via vues/matviews) |
| ETL / Scheduler | Python + Django commands + Cron |
| Auth | JWT (`djangorestframework-simplejwt`) + permissions Django (RBAC) |
| API doc | `drf-spectacular` (OpenAPI/Swagger) |
| Tests | pytest + pytest-django + factory_boy |
| Frontend | HTML, CSS, Bootstrap 5, Chart.js, DataTables |
| Rapports | ReportLab (PDF) + openpyxl (Excel) + CSV stdlib |

---

## 4. ARBORESCENCE DU PROJET (Phase 4)

```
Projet-Tutoré/
├── Docs/                                  # documents sources (inchangés)
├── docker-compose.yml                     # PostgreSQL 16 + (option) pgAdmin
├── .env.example                           # variables d'environnement
├── requirements.txt                       # dépendances Python
├── requirements-dev.txt                   # pytest, factories, flake8
├── manage.py
├── pytest.ini / setup.cfg                 # config pytest-django
├── cron.conf                              # tâches planifiées (ETL nocturne, recalcul KPI)
├── README-2.md                            # livrable final (install/config/run/test/deploy)
│
├── config/                                # projet Django (settings racine)
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│   └── celery... (non requis, cron utilisé)
│
├── apps/                                  # applications Django (modularité métier)
│   ├── common/                            # mixins, enums, base models, exceptions
│   ├── accounts/                          # Utilisateur, Étudiant, Enseignant, Resp., Admin, RBAC
│   │   └── (héritage : Utilisateur → Étudiant/Enseignant → Resp./Admin)
│   ├── academics/                         # UE, Semestre, Parcours, Résultat, Historique
│   ├── warehouse/                         # tables Dim_* + Fait_Résultats (schéma étoile)
│   ├── analytics/                         # moteur KPI (domain + services), agrégations
│   ├── risk/                              # ScoreRisque (formule 2.1), seuils, classification
│   ├── alerts/                            # Alerte, ParamètreAlerte, Recommandation
│   ├── etl/                               # Extract/Transform/Load + connecteur campusfaso.bf
│   ├── reporting/                         # PDF/Excel/CSV
│   ├── dashboards/                        # TB par profil (étudiant/enseignant/resp/admin)
│   └── audit/                             # journalisation + audit
│
├── domain/                                # MÉTIER PUR (sans Django) — formules & règles
│   ├── kpi/                               # score_risque.py (Eq 2.1), progression.py (Eq 2.2)
│   ├── thresholds.py                      # Faible/Modéré/Élevé
│   └── tests/                             # tests unitaires des formules (hors DB)
│
├── presentation/
│   ├── templates/                         # base.html, dashboards, rapports
│   ├── static/                            # bootstrap, chart.js, datatables, css, js
│   └── templatetags/
│
└── scripts/
    ├── entrypoint.sh                      # migrate + createsuperuser + seed démo
    └── seed_demo.py                       # données de démonstration (~maquettes du mémoire)
```

**Mapping BF → modules** (cohérent avec la Table 2.2 du mémoire « 6 modules ») :

| Module mémoire | Apps Django | BF couverts |
|----------------|-------------|-------------|
| Suivi Dossier | `academics`, `dashboards` | BF01, BF05, BF07 |
| Parcours | `analytics`, `dashboards` | BF06, BF09 |
| Score Décisionnel | `risk`, `analytics` | BF02, BF03, BF10 |
| Alertes | `alerts` | BF04, BF13 |
| Rapports | `reporting` | BF08, BF10 |
| Admin | `etl`, `accounts`, `audit` | BF11, BF12, BF13 |

---

## 5. PLAN DE DONNÉES & KPI (transition vers Phase 5)

### 5.1 Modèle relationnel (infrastructure)

Les modèles Django reflètent à la fois le **MCD** (entités métier normalisées) et le **schéma en étoile** (tables `Dim_*` / `Fait_Résultats` matérialisées par l'ETL). L'approche : les modèles OLTP (`Étudiant`, `UE`, `Semestre`, `RésultatAcadémique`, `Parcours`) sont la source de vérité issue de l'ETL ; les tables `Dim_*`/`Fait_*` sont des **vues matérialisées** ou des modèles miroir alimentés par l'ETL pour l'analyse multidimensionnelle.

### 5.2 Conventions
- `id` BigInt PK partout ; `created_at`/`updated_at` sur toutes les entités (audit).
- `matricule` UNIQUE ; `code_ue` UNIQUE.
- Index sur `(idEtudiant, idSemestre)`, `(idUE, idSemestre)`, `scoreRisque`.
- Toutes les formules KPI résident dans `domain/` (Python pur) → tests unitaires sans base de données.

---

## 6. POINTS D'AMBIGUÏTÉ TRAITÉS [DÉDUCTIONS]

| # | Ambiguïté | Décision |
|---|-----------|----------|
| D1 | Metabase vs interface maison | Interface Django + Charts.js (cahier des charges impose Bootstrap/Charts.js) ; Metabase documenté comme alternative |
| D2 | Airflow vs scheduler | Django commands + Cron (mémoire juge Airflow surdimensionné) |
| D3 | Schéma du DW : modèles ou vues ? | Modèles OLTP source + tables Dim/Fait (schéma étoile) alimentées par ETL |
| D4 | Connecteur campusfaso.bf (pas d'API documentée) | Adaptateur abstrait `CampusFasoClient` + implémentation mock/fixture pour démo + hooks pour API REST réelle (lecture seule) |
| D5 | Absentéisme non présent dans campusfaso | `A` calculé à partir d'un modèle `Présence` [DÉDUCTION], alimentable quand la source le permettra ; défaut 0 |
| D6 | Pondérations score | Exactement 0,40/0,30/0,20/0,10 (Eq 2.1), stockées dans `ParamètreAlerte`/`Configuration` pour calibration future |
| D7 | LDAP/SSO | Auth locale JWT par défaut, structure prévue pour LDAP (classe `CampusFasoLDAPBackend`) |
| D8 | BF14 référencé dans Table 2.2 mais absent du catalogue | [DÉDUCTION] BF14 = « Suivi longitudinal / timeline parcours » (cohérent avec le module Suivi Dossier) |

---

Ce document sera complété/affiné pendant l'implémentation. Il constitue la **référence de cohérence** entre tous les diagrammes.
