# SuiviCampus

> **Plateforme décisionnelle de suivi académique et de gestion des parcours étudiants**

SuiviCampus est une plateforme web conçue pour compléter les systèmes d'information universitaires en offrant un suivi académique global, des indicateurs décisionnels et des mécanismes d'alerte précoce afin d'améliorer l'accompagnement des étudiants tout au long de leur parcours universitaire.

Ce projet a été réalisé dans le cadre d'un mémoire de Licence en Informatique.

---

# Objectifs

SuiviCampus a pour objectif de :

* assurer un suivi longitudinal du parcours de chaque étudiant ;
* centraliser les données académiques provenant de plusieurs sources ;
* calculer des indicateurs clés de performance (KPI) ;
* détecter précocement les étudiants à risque ;
* générer automatiquement des alertes ;
* fournir des tableaux de bord décisionnels aux responsables pédagogiques.

---

# Fonctionnalités

## Gestion académique

* Consultation du parcours étudiant
* Historique des inscriptions
* Consultation des résultats académiques
* Suivi de la progression
* Visualisation des performances

## Analyse décisionnelle

* Calcul du score de risque académique
* Génération d'alertes automatiques
* Calcul des KPI
* Analyse statistique
* Suivi des cohortes

## Tableaux de bord

* Tableau de bord étudiant
* Tableau de bord enseignant
* Tableau de bord responsable pédagogique
* Indicateurs institutionnels

## Entrepôt de données

* Processus ETL
* Centralisation des données
* Historisation
* Préparation des données analytiques

---

# Architecture

Le projet suit une architecture en couches inspirée de la Clean Architecture.

```text
Utilisateurs
      │
      ▼
Frontend
      │
      ▼
Django REST API
      │
      ├── Authentification
      ├── Services métier
      ├── Calcul KPI
      ├── Moteur d'alertes
      └── Analytics
      │
      ▼
Data Warehouse
      ▲
      │
Processus ETL
      │
      ▼
Sources de données
```

---

# Technologies utilisées

## Backend

* Python 3
* Django 5
* Django REST Framework
* JWT Authentication

## Base de données

* PostgreSQL
* SQLite (développement)

## Analyse de données

* Pandas
* ETL Python

## Documentation

* LaTeX
* UML

## Déploiement

* Docker
* Docker Compose

---

# Structure du projet

```text
SuiviCampus/
├── apps/
├── config/
├── Docs/
├── domain/
├── presentation/
├── scripts/
├── tests_integration/
├── tex/
├── manage.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Installation

## Cloner le dépôt

```bash
git clone https://github.com/<utilisateur>/SuiviCampus.git

cd SuiviCampus
```

## Créer un environnement virtuel

```bash
python -m venv .venv
```

Linux

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

## Installer les dépendances

```bash
pip install -r requirements.txt
```

---

# Configuration

Créer un fichier `.env`.

Exemple :

```env
DEBUG=True

SECRET_KEY=your-secret-key

DATABASE_URL=postgresql://user:password@localhost:5432/suivicampus
```

---

# Migrations

```bash
python manage.py makemigrations

python manage.py migrate
```

---

# Création d'un superutilisateur

```bash
python manage.py createsuperuser
```

---

# Lancer le serveur

```bash
python manage.py runserver
```

Le serveur sera accessible à :

```
http://127.0.0.1:8000/
```

---

# Tests

Exécuter tous les tests :

```bash
pytest
```

Rapport de couverture :

```bash
pytest --cov
```

---

# Documentation

La documentation du projet est disponible dans :

* `Docs/`
* `tex/`
* `CONCEPTION.md`

---

# Cas d'utilisation principaux

* Suivi du parcours académique
* Calcul du score de risque
* Génération d'alertes
* Consultation des tableaux de bord
* Analyse des performances
* Aide à la décision pédagogique

---

# État du projet

Le projet comprend notamment :

* Architecture logicielle
* Modélisation UML
* Processus ETL
* Entrepôt de données
* Moteur d'analyse
* Calcul des KPI
* Génération d'alertes
* Documentation technique

---

# Feuille de route

* Interface utilisateur complète
* Authentification avancée
* Notifications en temps réel
* Tableaux de bord interactifs
* API documentée
* Déploiement en production

---

# Contribution

Les contributions sont les bienvenues.

1. Fork du projet.
2. Création d'une branche.
3. Développement des modifications.
4. Exécution des tests.
5. Création d'une Pull Request.

---

# Licence

Ce projet est distribué sous la licence MIT.

---

# Auteur

**Saki**

Projet réalisé dans le cadre d'un mémoire de Licence en Informatique portant sur la conception d'une plateforme décisionnelle de suivi académique et de gestion des parcours étudiants.
