"""Vues d'authentification web (login/logout) — session Django pour l'UI.

L'API utilise JWT ; l'interface web utilise la session Django (plus simple
pour le rendu côté serveur). Les deux coexistent.
"""
import logging
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


def home_view(request):
    """Page d'accueil publique (pas besoin d'être authentifié).
    
    Si l'utilisateur est déjà connecté, redirige vers son dashboard.
    Sinon, affiche la page d'accueil avec lien vers connexion.
    """
    logger.info(f"[HOME] Visite page accueil - Authentifié: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        logger.info(f"[HOME] Redirection -> {request.user.username}")
        return _redirect_par_role(request.user)
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Connexion à l'interface web (session)."""
    logger.info(f"[LOGIN] Méthode: {request.method} | IP: {request.META.get('REMOTE_ADDR')}")
    
    if request.user.is_authenticated:
        logger.info(f"[LOGIN] Déjà connecté: {request.user.username}")
        return _redirect_par_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        logger.info(f"[LOGIN] Tentative: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        logger.info(f"[LOGIN] Résultat: {user} | Actif: {getattr(user, 'is_active', 'N/A')}")
        
        if user is not None and user.is_active:
            logger.info(f"[LOGIN] ✅ SUCCÈS: {username} (ID:{user.pk})")
            django_login(request, user)
            logger.info(f"[LOGIN] Session: {request.session.session_key}")
            return _redirect_par_role(user)
        
        logger.warning(f"[LOGIN] ❌ ÉCHEC: {username}")
        return render(request, "login.html", {
            "error": "Identifiants invalides. Vérifiez votre nom d'utilisateur et mot de passe.",
            "username": username,
        })
    
    logger.info(f"[LOGIN] Affichage formulaire")
    return render(request, "login.html")


@login_required
def logout_view(request):
    """Déconnexion."""
    logger.info(f"[LOGOUT] Déconnexion: {request.user.username}")
    django_logout(request)
    return redirect(reverse("dashboards:login"))


@login_required
def accueil(request):
    """Redirige vers le tableau de bord du rôle de l'utilisateur (BF03)."""
    logger.info(f"[ACCUEIL] Redirection role: {getattr(request.user, 'role', 'inconnu')}")
    return _redirect_par_role(request.user)


def _redirect_par_role(user):
    """Redirige vers le dashboard adapté au rôle."""
    role = getattr(user, "role", "etudiant")
    logger.info(f"[REDIRECT] {user.username} -> role: {role}")
    
    if role == "administrateur":
        return redirect(reverse("dashboards:admin_etl"))
    if role == "responsable":
        return redirect(reverse("dashboards:responsable"))
    if role == "enseignant":
        return redirect(reverse("dashboards:enseignant"))
    return redirect(reverse("dashboards:etudiant"))