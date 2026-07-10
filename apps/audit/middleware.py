"""Middleware d'audit (BF sécurité).

Enregistre les actions sensibles (mutations API et admin) dans le
journal d'audit (AuditLog) pour traçabilité. Capture : utilisateur,
méthode HTTP, chemin, adresse IP, statut de la réponse.
"""
import logging

from apps.audit.models import AuditLog

logger = logging.getLogger("apps.audit")


class AuditMiddleware:
    """Journalise les requêtes mutatives (POST/PUT/PATCH/DELETE) sur l'API et l'admin.

    Conformément à CONCEPTION.md (couche security), les mutations sont tracées
    pour audit. La lecture n'est pas journalisée (trop volumineuse).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        method = request.method
        if method in ("POST", "PUT", "PATCH", "DELETE") and (
            request.path.startswith("/api/") or request.path.startswith("/admin/")
        ):
            user = getattr(request, "user", None)
            username = getattr(user, "username", "") or "anonymous"
            ip = _get_client_ip(request)
            statut = response.status_code
            detail = ""
            if statut >= 400:
                detail = f"Requête mutative échouée ({method})"

            # Log console
            logger.info(
                "AUDIT %s %s user=%s ip=%s status=%s",
                method, request.path, username, ip, statut,
            )
            # Persistance en base (BF sécurité)
            try:
                AuditLog.objects.create(
                    utilisateur=username,
                    action=method,
                    chemin=request.path[:255],
                    adresse_ip=ip,
                    statut=statut,
                    detail=detail,
                )
            except Exception:
                # Ne jamais planter la requête à cause de l'audit
                logger.exception("Échec de persistance du journal d'audit")
        return response


def _get_client_ip(request):
    """Récupère l'IP réelle du client (gère les proxies)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

