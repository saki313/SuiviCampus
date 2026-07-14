# apps/accounts/backends.py
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

logger = logging.getLogger('django.contrib.auth')

class TraceBackend(ModelBackend):
    """Backend avec traces détaillées"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"[BACKEND] Début authenticate: username={username}")
        
        # Récupère l'utilisateur
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=username)
            logger.debug(f"[BACKEND] Utilisateur trouvé: {user.pk}")
            logger.debug(f"[BACKEND] Password hash en base: {user.password!r}")
            logger.debug(f"[BACKEND] Password utilisable: {user.has_usable_password()}")
        except UserModel.DoesNotExist:
            logger.debug(f"[BACKEND] Utilisateur introuvable: {username}")
            return None
        
        # Vérifie le mot de passe
        password_ok = user.check_password(password)
        logger.debug(f"[BACKEND] Password check: {password_ok}")
        
        # Vérifie si actif
        logger.debug(f"[BACKEND] is_active: {user.is_active}")
        
        if password_ok and user.is_active:
            logger.info(f"[BACKEND] ✅ Retourne user: {username}")
            return user
        
        logger.warning(f"[BACKEND] ❌ Échec auth")
        return None
