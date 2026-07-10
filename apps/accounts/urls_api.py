"""Routes API REST — Comptes & profils (BF12)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api.views import (
    UtilisateurViewSet, ProfilEtudiantViewSet, ProfilEnseignantViewSet,
    ResponsablePedagogiqueViewSet, ProfilAdministrateurViewSet,
)

router = DefaultRouter()
router.register("utilisateurs", UtilisateurViewSet, basename="utilisateur")
router.register("etudiants", ProfilEtudiantViewSet, basename="etudiant")
router.register("enseignants", ProfilEnseignantViewSet, basename="enseignant")
router.register("responsables", ResponsablePedagogiqueViewSet, basename="responsable")
router.register("administrateurs", ProfilAdministrateurViewSet, basename="administrateur")

app_name = "accounts_api"
urlpatterns = [
    path("", include(router.urls)),
]
