"""Adaptateur API REST lecture-seule pour campusfaso.bf (D4).

[DEDUCTION D4] : campusfaso.bf n'expose pas d'API documentée publiquement.
Cette implémentation est volontairement générique (REST JSON standard) :
elle pourra être adaptée au schéma réel une fois celui-ci documenté.
L'ETL reste strictement en lecture seule.
"""
from __future__ import annotations

import logging
from typing import Iterable

import requests

from .base import (
    CampusFasoClient, SourceEtudiant, SourceUE, SourceResultat,
)

logger = logging.getLogger("apps.etl")


class ApiCampusFasoClient(CampusFasoClient):
    """Client REST lecture-seule pour service.campusfaso.bf.

    NB : non utilisé par défaut (ETL_SOURCE_MODE=mock). Activé en production
    si la source expose une API. Adaptateurs à ajuster au schéma réel.
    """

    def __init__(self, base_url: str, token: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self):
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, endpoint: str, params: dict | None = None) -> list:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(
                url, headers=self._headers(), params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Échec extraction %s : %s", url, e)
            raise

    def health_check(self) -> bool:
        try:
            self._get("/api/health")
            return True
        except Exception:
            return False

    def extract_etudiants(self, since: str | None = None) -> Iterable[SourceEtudiant]:
        params = {"modified_since": since} if since else None
        for row in self._get("/api/etudiants", params):
            yield SourceEtudiant(**row)

    def extract_ues(self) -> Iterable[SourceUE]:
        for row in self._get("/api/ue"):
            yield SourceUE(**row)

    def extract_resultats(self, since: str | None = None) -> Iterable[SourceResultat]:
        params = {"modified_since": since} if since else None
        for row in self._get("/api/resultats", params):
            yield SourceResultat(**row)
