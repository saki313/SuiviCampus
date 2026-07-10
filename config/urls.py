"""Routage racine — Plateforme de Suivi Académique.

  /                → interface web (presentation layer)
  /admin/          → back-office Django (gestion / audit)
  /api/            → API REST (DRF)
  /api/docs/       → Swagger UI (drf-spectacular)
  /api/schema/     → schéma OpenAPI brut
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Racine → redirection vers le tableau de bord (rôle-dépendant)
    path("", RedirectView.as_view(url="/tableau-de-bord/", permanent=False), name="home"),

    # Interface web (presentation layer) — incluse AVANT admin.site.urls car
    # les URLs dashboards admin sont préfixées /admin/ (ex: /admin/etl/).
    # Django résout les URLs dans l'ordre : dashboards doit être testé en premier.
    path("", include("apps.dashboards.urls")),

    # Back-office Django (administrateur)
    path("admin/", admin.site.urls),

    # API REST — JWT
    path("api/auth/", include("apps.accounts.urls_auth")),

    # API REST — ressources métier
    path("api/", include("apps.accounts.urls_api")),
    path("api/", include("apps.academics.urls_api")),
    path("api/", include("apps.warehouse.urls_api")),
    path("api/", include("apps.analytics.urls_api")),
    path("api/", include("apps.risk.urls_api")),
    path("api/", include("apps.alerts.urls_api")),
    path("api/", include("apps.reporting.urls_api")),
    path("api/", include("apps.etl.urls_api")),

    # Documentation API (Swagger / Redoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
