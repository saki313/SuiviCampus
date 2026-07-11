"""Vues d'authentification web (login/logout) — session Django pour l'UI.

L'API utilise JWT ; l'interface web utilise la session Django (plus simple
pour le rendu côté serveur). Les deux coexistent.
"""
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods


def home_view(request):
    """Page d'accueil publique (pas besoin d'être authentifié).
    
    Si l'utilisateur est déjà connecté, redirige vers son dashboard.
    Sinon, affiche la page d'accueil avec lien vers connexion.
    """
    if request.user.is_authenticated:
        return _redirect_par_role(request.user)
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Connexion à l'interface web (session)."""
    if request.user.is_authenticated:
        return _redirect_par_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            django_login(request, user)
            return _redirect_par_role(user)
        return render(request, "login.html", {
            "error": "Identifiants invalides. Vérifiez votre nom d'utilisateur et mot de passe.",
            "username": username,
        })
    return render(request, "login.html")


@login_required
def logout_view(request):
    """Déconnexion."""
    django_logout(request)
    return redirect(reverse("dashboards:login"))


@login_required
def accueil(request):
    """Redirige vers le tableau de bord du rôle de l'utilisateur (BF03)."""
    return _redirect_par_role(request.user)


def _redirect_par_role(user):
    """Redirige vers le dashboard adapté au rôle."""
    role = getattr(user, "role", "etudiant")
    if role == "administrateur":
        return redirect(reverse("dashboards:admin_etl"))
    if role == "responsable":
        return redirect(reverse("dashboards:responsable"))
    if role == "enseignant":
        return redirect(reverse("dashboards:enseignant"))
    return redirect(reverse("dashboards:etudiant"))
