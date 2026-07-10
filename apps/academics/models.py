"""Modèles académiques — entités OLTP issues de l'ETL (mémoire §2.2.2, Fig 2.8).

Ces modèles sont la source de vérité opérationnelle : ils sont alimentés par
le moteur ETL à partir de service.campusfaso.bf (lecture seule).

Entités : UniteEnseignement, Semestre, ParcoursAcademique, ResultatAcademique,
          HistoriqueAcademique, Presence.
"""
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.enums import SessionExamen
from apps.accounts.models import ProfilEtudiant


class UniteEnseignement(TimeStampedModel):
    """Unite d'Enseignement (UE) — reference des enseignements (memoire MCD).

    Attributs du dictionnaire des donnees + schema DW Dim_UE :
        code (PK logique, unique), intitule, credits ECTS, semestre, type (obligatoire/optionnel).
    """
    code = models.CharField("Code UE", max_length=20, unique=True, db_index=True)
    intitule = models.CharField("Intitule", max_length=200)
    credits = models.PositiveSmallIntegerField("Credits ECTS", default=3)
    semestre_numero = models.PositiveSmallIntegerField("Numero de semestre", default=1)
    ue_type = models.CharField(
        "Type", max_length=15, choices=[("obligatoire", "Obligatoire"), ("optionnel", "Optionnel")],
        default="obligatoire",
    )

    class Meta:
        db_table = "unite_enseignement"
        verbose_name = "Unite d'Enseignement"
        verbose_name_plural = "Unites d'Enseignement"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.intitule}"


class Semestre(TimeStampedModel):
    """Semestre academique — periode de reference (memoire MCD, DW Dim_Semestre).

    Attributs : numero, annee, dateDebut, dateFin.
    """
    numero = models.PositiveSmallIntegerField("Numero")
    annee = models.PositiveSmallIntegerField("Annee")  # ex. 2025
    annee_scolaire = models.CharField("Annee scolaire", max_length=9, default="")  # "2025-2026"
    date_debut = models.DateField("Date de debut", null=True, blank=True)
    date_fin = models.DateField("Date de fin", null=True, blank=True)

    class Meta:
        db_table = "semestre"
        verbose_name = "Semestre"
        verbose_name_plural = "Semestres"
        unique_together = [("numero", "annee")]
        ordering = ["annee", "numero"]

    def __str__(self):
        return f"S{self.numero} — {self.annee_scolaire}"


class ParcoursAcademique(TimeStampedModel):
    """Parcours academique d'un etudiant — aggrege les resultats (composition Fig 2.2).

    Composition : ParcoursAcademique dia-> ResultatAcademique
    Attributs : etudiant, annee_scolaire, filiere, niveau, statut (en_cours/diplome/abandon).
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="parcours", verbose_name="Etudiant",
    )
    annee_scolaire = models.CharField("Annee scolaire", max_length=9, default="")
    filiere = models.CharField("Filiere", max_length=100, blank=True, default="")
    niveau = models.CharField("Niveau", max_length=5, blank=True, default="")
    statut = models.CharField(
        "Statut", max_length=15,
        choices=[("en_cours", "En cours"), ("diplome", "Diplome"), ("abandon", "Abandon")],
        default="en_cours",
    )

    class Meta:
        db_table = "parcours_academique"
        verbose_name = "Parcours academique"
        verbose_name_plural = "Parcours academiques"
        ordering = ["etudiant__matricule", "-annee_scolaire"]
        indexes = [
            # Filtrage BF09 (redoublements/réorientations) : parcours__statut.
            models.Index(fields=["statut"], name="idx_parcours_statut"),
        ]

    def __str__(self):
        return f"{self.etudiant.matricule} — {self.annee_scolaire}"


class ResultatAcademique(TimeStampedModel):
    """Resultat academique — note d'un etudiant dans une UE a un semestre (Fait).

    Alimente Fait_Resultats du DW apres transformation ETL.
    Attributs : etudiant, ue, semestre, note (Decimal/20), credits, valide (bool),
                session_examen, date_evaluation.
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="resultats", verbose_name="Etudiant",
        db_index=True,
    )
    ue = models.ForeignKey(
        UniteEnseignement, on_delete=models.PROTECT,
        related_name="resultats", verbose_name="UE",
    )
    semestre = models.ForeignKey(
        Semestre, on_delete=models.PROTECT,
        related_name="resultats", verbose_name="Semestre",
    )
    note = models.DecimalField("Note /20", max_digits=5, decimal_places=2)
    credits = models.PositiveSmallIntegerField("Credits obtenus", default=0)
    valide = models.BooleanField("Valide", default=False)
    session = models.CharField(
        "Session", max_length=15, choices=SessionExamen.choices, default=SessionExamen.NORMALE
    )
    date_evaluation = models.DateField("Date d'evaluation", null=True, blank=True)

    class Meta:
        db_table = "resultat_academique"
        verbose_name = "Resultat academique"
        verbose_name_plural = "Resultats academiques"
        unique_together = [("etudiant", "ue", "semestre", "session")]
        ordering = ["etudiant__matricule", "semestre__annee", "ue__code"]
        indexes = [
            models.Index(fields=["etudiant", "semestre"], name="idx_res_etu_sem"),
            models.Index(fields=["ue", "semestre"], name="idx_res_ue_sem"),
        ]

    def __str__(self):
        return f"{self.etudiant.matricule} | {self.ue.code} | {self.note}/20"


class HistoriqueAcademique(TimeStampedModel):
    """Historique academique consolide d'un etudiant (BF07).

    Pre-enregistre les snapshots de parcours pour consultation longitudinale.
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="historique", verbose_name="Etudiant",
    )
    semestre = models.ForeignKey(
        Semestre, on_delete=models.PROTECT,
        related_name="historiques", verbose_name="Semestre",
    )
    moyenne_generale = models.DecimalField(
        "Moyenne generale /20", max_digits=5, decimal_places=2, null=True, blank=True
    )
    credits_total = models.PositiveIntegerField("Credits total vises", default=0)
    credits_acquis = models.PositiveIntegerField("Credits acquis", default=0)
    ues_total = models.PositiveSmallIntegerField("UEs total", default=0)
    ues_echec = models.PositiveSmallIntegerField("UEs en echec", default=0)
    sessions_total = models.PositiveSmallIntegerField("Seances total", default=0)
    sessions_presentes = models.PositiveSmallIntegerField("Seances presentes", default=0)

    class Meta:
        db_table = "historique_academique"
        verbose_name = "Historique academique"
        verbose_name_plural = "Historiques academiques"
        unique_together = [("etudiant", "semestre")]
        ordering = ["etudiant__matricule", "-semestre__annee"]

    def __str__(self):
        return f"Hist. {self.etudiant.matricule} S{self.semestre}"


class Presence(TimeStampedModel):
    """Presence / absences — alimente le calcul d'absenteisme (indic. A, Eq 2.1).

    [DEDUCTION D5] : campusfaso.bf ne fournit pas explicitement les presences ;
    ce modele permet de les saisir ou de les importer quand la source le permettra.
    Par defaut, A=0 dans le score de risque.
    """
    etudiant = models.ForeignKey(
        ProfilEtudiant, on_delete=models.CASCADE,
        related_name="presences", verbose_name="Etudiant",
    )
    ue = models.ForeignKey(
        UniteEnseignement, on_delete=models.PROTECT,
        related_name="presences", verbose_name="UE",
    )
    date_cours = models.DateField("Date du cours")
    present = models.BooleanField("Present", default=True)

    class Meta:
        db_table = "presence"
        verbose_name = "Presence"
        verbose_name_plural = "Presences"
        unique_together = [("etudiant", "ue", "date_cours")]
        ordering = ["date_cours", "etudiant__matricule"]
        indexes = [
            # Agrégations d'absentéisme (indicateur A, Eq 2.1) filtrant par étudiant.
            models.Index(fields=["etudiant"], name="idx_presence_etu"),
        ]

    def __str__(self):
        statut = "P" if self.present else "A"
        return f"{self.etudiant.matricule} {self.ue.code} {self.date_cours} [{statut}]"
