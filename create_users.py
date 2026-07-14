# create_users.py — à lancer avec : python manage.py shell < create_users.py
from apps.accounts.models import (
    Utilisateur, ProfilEnseignant, ResponsablePedagogique, ProfilAdministrateur,
)

PASSWORD = "MotDePasse123!"

# ========================================================================
# 1. ENSEIGNANT
# ========================================================================
ens_user = Utilisateur.objects.create_user(
    username="prof.kabore",
    email="prof.kabore@campusfaso.bf",
    password=PASSWORD,
    first_name="Boukary",
    last_name="KABORE",
    role="enseignant",
    telephone="+226 70 00 00 01",
)
ProfilEnseignant.objects.create(
    utilisateur=ens_user,
    departement="Informatique",
    specialite="Bases de données",
    grade="Maître de conférences",
)
print(f"✓ Enseignant créé : {ens_user.username}")

# ========================================================================
# 2. RESPONSABLE PÉDAGOGIQUE
#    (un responsable EST un enseignant + responsabilités)
# ========================================================================
resp_user = Utilisateur.objects.create_user(
    username="resp.sanou",
    email="resp.sanou@campusfaso.bf",
    password=PASSWORD,
    first_name="Issouf",
    last_name="SANOU",
    role="responsable",
    telephone="+226 70 00 00 02",
)
resp_profil = ProfilEnseignant.objects.create(
    utilisateur=resp_user,
    departement="Informatique",
    specialite="Réseaux",
    grade="Professeur titulaire",
)
ResponsablePedagogique.objects.create(
    enseignant=resp_profil,
    filiere_geree="Informatique",
    niveau_gere="L1",
)
print(f"✓ Responsable créé : {resp_user.username}")

# ========================================================================
# 3. ADMINISTRATEUR
# ========================================================================
admin_user = Utilisateur.objects.create_user(
    username="admin.traore",
    email="admin.traore@campusfaso.bf",
    password=PASSWORD,
    first_name="Awa",
    last_name="TRAORE",
    role="administrateur",
    telephone="+226 70 00 00 03",
    is_staff=True,   # accès Django admin
    is_superuser=True,
)
ProfilAdministrateur.objects.create(
    utilisateur=admin_user,
    service="Informatique",
)
print(f"✓ Administrateur créé : {admin_user.username}")

print("\n=== Récapitulatif ===")
print(f"Enseignants  : {Utilisateur.objects.filter(role='enseignant').count()}")
print(f"Responsables: {Utilisateur.objects.filter(role='responsable').count()}")
print(f"Admins      : {Utilisateur.objects.filter(role='administrateur').count()}")
