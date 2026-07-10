"""Routes de l'interface web (presentation layer).

Toutes les URLs de l'interface web sont préfixées par '/' (racine).
L'API REST est sous /api/.
"""
from django.urls import path

from . import views_auth, views_etudiant, views_enseignant, views_admin, views_rapports

app_name = "dashboards"

urlpatterns = [
    # Auth
    path("login/", views_auth.login_view, name="login"),
    path("logout/", views_auth.logout_view, name="logout"),
    path("", views_auth.accueil, name="accueil"),

    # Tableau de bord Étudiant
    path("tableau-de-bord/", views_etudiant.dashboard_etudiant, name="etudiant"),
    path("mon-parcours/", views_etudiant.parcours_etudiant, name="etudiant_parcours"),
    path("mes-alertes/", views_etudiant.alertes_etudiant, name="etudiant_alertes"),

    # Tableau de bord Enseignant
    path("enseignant/", views_enseignant.dashboard_enseignant, name="enseignant"),
    path("etudiants/", views_enseignant.liste_etudiants, name="etudiants_liste"),

    # Tableau de bord Responsable
    path("pilotage/", views_enseignant.dashboard_responsable, name="responsable"),
    path("rapports/", views_enseignant.rapports_view, name="rapports"),

    # Tableau de bord Administrateur
    path("admin/etl/", views_admin.admin_etl, name="admin_etl"),
    path("admin/utilisateurs/", views_admin.admin_utilisateurs, name="admin_utilisateurs"),
    path("admin/parametres/", views_admin.admin_parametres, name="admin_parametres"),
    path("admin/audit/", views_admin.admin_audit, name="admin_audit"),

    # Rapports — téléchargements (BF08)
    path("rapports/pdf/", views_rapports.telecharger_pdf, name="rapport_pdf"),
    path("rapports/excel/", views_rapports.telecharger_excel, name="rapport_excel"),
    path("rapports/csv/", views_rapports.telecharger_csv, name="rapport_csv"),
]
