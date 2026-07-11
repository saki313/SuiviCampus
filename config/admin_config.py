"""Configuration personnalisée du Django admin pour la plateforme.

Ajoute des liens de navigation pour revenir au site principal et améliore l'UX.
"""
from django.contrib import admin
from django.urls import reverse


class CustomAdminSite(admin.AdminSite):
    """Site admin personnalisé avec lien de retour vers le site principal."""
    
    site_header = "Suivi Académique — Administration"
    site_title = "Suivi Académique Admin"
    index_title = "Gestion du système"

    def index(self, request, extra_context=None):
        """Ajoute un lien vers le site principal dans la vue d'accueil."""
        extra_context = extra_context or {}
        extra_context["site_url"] = "/"
        extra_context["site_name"] = "Retour au site"
        return super().index(request, extra_context=extra_context)

    def each_context(self, request):
        """Ajoute le lien "Voir le site" dans chaque contexte admin."""
        context = super().each_context(request)
        context["site_url"] = "/"
        context["site_name"] = "Suivi Académique"
        return context


# Remplace le site admin par défaut
admin.site = CustomAdminSite(name="admin")
