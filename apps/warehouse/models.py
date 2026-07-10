"""Modeles du Data Warehouse — schema en etoile (Fig 2.8, memoire §2.4.3).

Alimentes par le moteur ETL (Phase 9) a partir des modeles OLTP (academics).
Les tables Dim_* et Fait_Resultats constituent le DW decisionnel.

Schema en etoile :
    Fait_Resultats (table de faits centrale)
        -> Dim_Etudiant
        -> Dim_UE
        -> Dim_Semestre
        -> Dim_Temps
"""
from django.db import models

from apps.common.models import TimeStampedModel


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

class DimEtudiant(TimeStampedModel):
    """Dimension Etudiant du DW (Fig 2.8).

    Attributs : idEtudiant(PK), matricule, niveauActuel, filiere, promotion.
    Alimentee par ETL a partir de ProfilEtudiant + ParcoursAcademique.
    """
    source_id = models.PositiveIntegerField("ID source (ProfilEtudiant)", unique=True)
    matricule = models.CharField("Matricule", max_length=20, db_index=True)
    niveau_actuel = models.CharField("Niveau actuel", max_length=5, default="")
    filiere = models.CharField("Filiere", max_length=100, blank=True, default="")
    promotion = models.CharField("Promotion", max_length=20, blank=True, default="")
    annee_scolaire = models.CharField("Annee scolaire", max_length=9, default="")

    class Meta:
        db_table = "dim_etudiant"
        verbose_name = "Dim — Etudiant"
        verbose_name_plural = "Dim — Etudiants"
        ordering = ["matricule"]

    def __str__(self):
        return f"DimEtu:{self.matricule}"


class DimUE(TimeStampedModel):
    """Dimension UE du DW (Fig 2.8).

    Attributs : idUE(PK), code, intitule, credits, semestre.
    """
    source_id = models.PositiveIntegerField("ID source (UniteEnseignement)", unique=True)
    code = models.CharField("Code UE", max_length=20, db_index=True)
    intitule = models.CharField("Intitule", max_length=200, blank=True, default="")
    credits = models.PositiveSmallIntegerField("Credits ECTS", default=3)
    semestre = models.PositiveSmallIntegerField("Numero semestre", default=1)

    class Meta:
        db_table = "dim_ue"
        verbose_name = "Dim — UE"
        verbose_name_plural = "Dim — UEs"
        ordering = ["code"]

    def __str__(self):
        return f"DimUE:{self.code}"


class DimSemestre(TimeStampedModel):
    """Dimension Semestre du DW (Fig 2.8).

    Attributs : idSemestre(PK), numero, annee, dateDebut, dateFin.
    """
    source_id = models.PositiveIntegerField("ID source (Semestre)", unique=True)
    numero = models.PositiveSmallIntegerField("Numero")
    annee = models.PositiveSmallIntegerField("Annee")
    date_debut = models.DateField("Date debut", null=True, blank=True)
    date_fin = models.DateField("Date fin", null=True, blank=True)

    class Meta:
        db_table = "dim_semestre"
        verbose_name = "Dim — Semestre"
        verbose_name_plural = "Dim — Semestres"
        ordering = ["annee", "numero"]

    def __str__(self):
        return f"DimSem:S{self.numero}-{self.annee}"


class DimTemps(TimeStampedModel):
    """Dimension Temps du DW (Fig 2.8).

    Attributs : idTemps(PK), annee, mois, sessionExamen, anneeScolaire.
    """
    annee = models.PositiveSmallIntegerField("Annee")
    mois = models.PositiveSmallIntegerField("Mois", null=True, blank=True)
    session_examen = models.CharField(
        "Session", max_length=15,
        choices=[("normale", "Normale"), ("rattrapage", "Rattrapage")],
        default="normale",
    )
    annee_scolaire = models.CharField("Annee scolaire", max_length=9, default="")

    class Meta:
        db_table = "dim_temps"
        verbose_name = "Dim — Temps"
        verbose_name_plural = "Dim — Temps"
        ordering = ["annee", "mois"]

    def __str__(self):
        return f"DimTemps:{self.annee}/{self.mois or '?'}"


# ---------------------------------------------------------------------------
# Table de faits
# ---------------------------------------------------------------------------

class FaitResultats(TimeStampedModel):
    """Table de faits centrale du DW (Fig 2.8).

    Attributs : idEtudiant(FK), idUE(FK), idSemestre(FK), idTemps(FK),
                note(Decimal), credits(Integer), valide(Boolean), scoreRisque(Float).

    Le scoreRisque est calcule et ecrit ici par le moteur KPI (Eq 2.1).
    """
    etudiant = models.ForeignKey(
        DimEtudiant, on_delete=models.PROTECT,
        related_name="faits", verbose_name="Etudiant",
    )
    ue = models.ForeignKey(
        DimUE, on_delete=models.PROTECT,
        related_name="faits", verbose_name="UE",
    )
    semestre = models.ForeignKey(
        DimSemestre, on_delete=models.PROTECT,
        related_name="faits", verbose_name="Semestre",
    )
    temps = models.ForeignKey(
        DimTemps, on_delete=models.PROTECT,
        related_name="faits", verbose_name="Temps",
        null=True, blank=True,
    )
    note = models.DecimalField("Note /20", max_digits=5, decimal_places=2)
    credits = models.PositiveSmallIntegerField("Credits", default=0)
    valide = models.BooleanField("Valide", default=False)
    score_risque = models.FloatField("Score de risque [0-100]", null=True, blank=True)

    class Meta:
        db_table = "fait_resultats"
        verbose_name = "Fait — Resultats"
        verbose_name_plural = "Fait — Resultats"
        ordering = ["etudiant__matricule", "semestre__annee", "ue__code"]
        indexes = [
            models.Index(fields=["etudiant", "semestre"], name="idx_fait_etu_sem"),
            models.Index(fields=["ue", "semestre"], name="idx_fait_ue_sem"),
            models.Index(fields=["score_risque"], name="idx_fait_score"),
        ]

    def __str__(self):
        return f"Fait:{self.etudiant.matricule}|{self.ue.code}|{self.note}"
