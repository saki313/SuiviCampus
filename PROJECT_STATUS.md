# PROJECT_STATUS.md

> **Statut du projet**
>
> Projet : Plateforme Décisionnelle de Suivi Académique
>
> Ce document représente l'état officiel du projet. Il doit être lu avant toute modification du code.

---

# RÈGLE ABSOLUE

Le projet est basé sur une conception validée.

Les documents de référence sont :

1. CONCEPTION.md
2. Memoire.pdf
3. Diagrammes UML
4. Ce fichier PROJECT_STATUS.md

Aucune décision d'architecture ne doit être modifiée sans justification.

Ne jamais recréer une fonctionnalité déjà existante.

Toujours analyser le projet avant de coder.

---

# OBJECTIF

Développer une plateforme décisionnelle de suivi académique destinée à compléter la plateforme Campus Faso.

La plateforme :

- lit les données provenant de Campus Faso
- ne modifie jamais Campus Faso
- alimente un Data Warehouse PostgreSQL
- calcule les KPI académiques
- calcule le score de risque
- génère des alertes
- produit des tableaux de bord
- produit des rapports PDF / Excel / CSV

---

# ARCHITECTURE

Architecture figée.

Campus Faso

↓

ETL

↓

PostgreSQL (Data Warehouse)

↓

Services métier

↓

API REST

↓

Interface Web

---

# TECHNOLOGIES

Backend

- Python
- Django 5
- Django REST Framework
- PostgreSQL
- JWT
- drf-spectacular

Frontend

- Bootstrap 5
- Charts.js
- DataTables

Rapports

- ReportLab
- openpyxl

Tests

- pytest
- pytest-django

---

# RÈGLES D'ARCHITECTURE

Toujours respecter :

- Clean Architecture
- séparation des couches
- Domain indépendant de Django
- aucune logique métier dans Views
- aucune logique métier dans Serializers
- aucune logique métier dans Templates

La logique métier appartient uniquement :

- domain/
- services/

---

# FORMULES MÉTIER

Ne jamais modifier.

Score de risque :

0.40 × Notes

+ 0.30 × Crédits

+ 0.20 × UE validées

+ 0.10 × Assiduité

Valeur bornée entre 0 et 100.

Classification :

Faible : ≤ 30

Modéré : 31–60

Élevé : > 60

Toutes les pondérations restent configurables.

---

# ÉTAT DES PHASES

## Phase 1

Conception

✅ Terminée

---

## Phase 2

Architecture

✅ Terminée

---

## Phase 3

Documentation

✅ Terminée

---

## Phase 4

Validation conception

✅ Terminée

---

## Phase 5

Initialisation projet

État :

✅ Docker Compose

✅ PostgreSQL

✅ Configuration Django

✅ Settings base/dev/prod

✅ Requirements

✅ Structure du projet

✅ Applications créées

---

## Phase 6

Modèles

État :

✅ Modèles principaux

✅ Migrations

✅ Schéma Data Warehouse

✅ Data Warehouse opérationnel

---

## Phase 7

Domaine métier

État :

✅ Score de risque

✅ Progression

✅ Thresholds

✅ Services

✅ Tests unitaires

≈ 50 tests réussis

---

## Phase 8

API

État :

✅ JWT

✅ RBAC

✅ Permissions

✅ Serializers

✅ ViewSets

✅ Swagger

En grande partie terminé.

---

## Phase 9

ETL

État :

✅ CampusFasoClient abstrait

✅ MockCampusFasoClient

✅ Fixtures réalistes

≈85 étudiants

≈1020 résultats

≈5100 présences

✅ Pipeline ETL

✅ Historisation

✅ Synchronisation

✅ Chargement DW

✅ Management Command

python manage.py etl_run

Le pipeline fonctionne.

---

## Phase 10

KPI

État :

✅ Calcul automatique

✅ Génération alertes

✅ Recalcul après ETL

Fonctionnel.

---

## Phase 11

Dashboards

État : ✅ Terminée

Tous les dashboards implémentés et fonctionnels :

- base.html (Bootstrap 5, navigation par rôle, dark mode)
- login.html
- Dashboard Étudiant (score, progression, crédits, alertes, UE échec)
- Parcours étudiant (DataTables)
- Alertes étudiant (DataTables + badges)
- Dashboard Enseignant (KPI + donut Chart.js + UE critiques)
- Dashboard Responsable (KPI + bar Chart.js + alertes + UE critiques)
- Liste étudiants (DataTables + badges risque)
- Dashboard Administrateur (ETL, utilisateurs, paramètres, audit)
- Page rapports (filtres + téléchargements)
- CSS et JS applicatifs complets

---

## Phase 12

Rapports

État : ✅ Terminée

Formats implémentés :

- PDF (ReportLab) — synthèse académique : page de garde, KPI, tableau étudiants, UE critiques
- Excel (openpyxl) — 3 feuilles : Synthèse, Résultats, Alertes
- CSV (stdlib) — 18 colonnes d'indicateurs par étudiant

Services : apps/reporting/services/pdf_export.py, excel_export.py, csv_export.py

Vues web : apps/dashboards/views_rapports.py (/rapports/pdf/, excel/, csv/)

Vues API : apps/reporting/api/ (/api/rapports/pdf/, excel/, csv/)

Filtres : filiere et niveau applicables aux 3 formats

---

## Phase 13

Tests

État : ✅ Terminée

134 tests passés :

- Domaine KPI : 50 tests (score risque, progression, seuils)
- ETL mock : 10 tests (client mock, données, déterminisme)
- ETL pipeline : 12 tests (chargement OLTP/DW, idempotence, différentiel)
- Analytics : 7 tests (calcul indicateurs, persistance, promotion)
- Risk service : 8 tests (score, distribution, UE critiques)
- Alertes : 9 tests (génération, non-duplication, traitement, archivage)
- API REST : 10 tests (JWT, RBAC, permissions, endpoints)
- Reporting : 13 tests (PDF, Excel, CSV — format, contenu, filtres)
- Dashboards : 15 tests (login, RBAC web, téléchargements)

Configuration test : config/settings/test.py (SQLite en mémoire)

---

## Phase 14

Validation

État : ✅ Terminée

6 tests d'intégration validant les flux critiques :

- DS3 — ETL : extraction → chargement OLTP + DW (schéma étoile)
- DS1 — KPI : calcul score risque (Eq 2.1) + progression (Eq 2.2) + persistance
- DS2 — Alertes : génération + recommandations + non-duplication
- Rapports : PDF/Excel/CSV fonctionnels après scénario complet
- Bornage : tous les scores ∈ [0; 100]
- Idempotence : double passage ne crée pas de doublons

Corrections apportées lors de la validation :

- Bug URL : réordonnancement des routes (dashboards avant admin.site.urls)
- Incohérence : middleware d'audit persiste désormais en base (AuditLog)

Total : 140 tests passés (50 domain + 10 ETL mock + 12 ETL pipeline + 7 analytics
+ 8 risk + 9 alerts + 10 API + 13 reporting + 15 dashboards + 6 intégration)

---

## Phase 15

Optimisation

État : ✅ Terminée

Index de base de données ajoutés (migration 0002) :

- IndicateurAcademique : idx_indic_etu_sem (etudiant, semestre) — lookup principal KPI
- IndicateurAcademique : idx_indic_class_sem (classification_risque, semestre) — filtres TB
- Presence : idx_presence_etu — agrégations absentéisme (Eq 2.1)
- ParcoursAcademique : idx_parcours_statut — filtres BF09 redoublements

Optimisations de requêtes :

- _taux_reussite() : helper dédié (1 requête aggregate au lieu de 2)
- dashboard_enseignant : élimination du double count() sur ResultatAcademique
- dashboard_responsable : même correction, réutilisation du helper
- liste_etudiants : prefetch_related via Prefetch(to_attr) au lieu d'un dict en mémoire
- admin_utilisateurs : select_related sur les 3 profils liés

Pagination API : déjà configurée (PageNumberPagination, PAGE_SIZE=25)

Tests de performance : 8 tests ajoutés (tests_integration/test_performance.py)

- Recalcul KPI promotion (85 étudiants) < 3 s
- Distribution scores < 1 s
- UE critiques < 1 s
- Scores promotion (eval complète) < 1.5 s
- Calcul 1 étudiant < 200 ms
- Export CSV < 3 s
- Export Excel < 3 s
- Export PDF < 3 s

Total : 148 tests passés

Corrections apportées lors de l'optimisation :

- pytest.ini : DJANGO_SETTINGS_MODULE corrigé (config.settings.dev → config.settings.test)

---

## Phase 16

Préparation déploiement

À faire.

---

## Phase 17

Livraison

À faire.

---

# DONNÉES DE DÉMONSTRATION

Le projet possède actuellement :

≈85 étudiants

≈12 UE

≈1020 résultats

≈5100 présences

Les KPI sont calculés.

Les alertes sont générées.

Le Data Warehouse est alimenté.

---

# COMMANDES IMPORTANTES

Lancer PostgreSQL

docker-compose up -d

Lancer Django

python manage.py runserver

ETL

python manage.py etl_run

Calcul KPI

python manage.py kpi_compute

Tests

pytest

Contrôle Django

python manage.py check

Migrations

python manage.py migrate

---

# MÉTHODE DE TRAVAIL

Avant toute modification :

1. Lire CONCEPTION.md

2. Lire ce fichier

3. Explorer le projet

4. Identifier les fonctionnalités déjà implémentées

5. Continuer uniquement la phase en cours

Ne jamais repartir de zéro.

Ne jamais remplacer une implémentation fonctionnelle.

Toujours compléter le travail existant.

---

# PHASE ACTUELLE

Phase en cours :

Phase 16

Objectif :

Préparation au déploiement :

- Scripts de déploiement (entrypoint.sh, gunicorn)
- Configuration production (Gunicorn, PostgreSQL, collectstatic)
- Documentation README-2.md (install/config/run/test/deploy)
- Vérification sécurité (HTTPS, HSTS, CSRF)
- Sauvegarde et restore de la base

Une fois cette phase validée, poursuivre avec la livraison (Phase 17).

---

# IMPORTANT

À chaque reprise du projet :

- analyser le code existant avant toute modification ;
- respecter strictement la conception ;
- vérifier que le projet compile ;
- exécuter les tests concernés ;
- corriger les erreurs avant de continuer.

Le projet doit rester exécutable après chaque étape.
