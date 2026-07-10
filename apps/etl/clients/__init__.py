"""Adaptateurs de source ETL (campusfaso.bf).

Factory `get_client()` : sélectionne le client selon ETL_SOURCE_MODE :
  - "mock" (défaut) : MockCampusFasoClient (fixtures locales réalistes)
  - "api"           : ApiCampusFasoClient (vrai endpoint lecture-seule)
"""
from django.conf import settings

from .base import (
    CampusFasoClient, SourceEtudiant, SourceUE, SourceResultat, SourcePresence,
)
from .mock import MockCampusFasoClient


def get_client() -> CampusFasoClient:
    """Sélectionne le client ETL selon la configuration."""
    mode = getattr(settings, "ETL_SOURCE_MODE", "mock")
    if mode == "api":
        # Branchement futur : importer ApiCampusFasoClient ici (D4)
        from .api import ApiCampusFasoClient
        return ApiCampusFasoClient(
            base_url=getattr(settings, "ETL_CAMPUSFASO_BASE_URL", ""),
            token=getattr(settings, "ETL_CAMPUSFASO_API_TOKEN", ""),
        )
    return MockCampusFasoClient()


__all__ = [
    "CampusFasoClient", "SourceEtudiant", "SourceUE",
    "SourceResultat", "SourcePresence",
    "MockCampusFasoClient", "get_client",
]
