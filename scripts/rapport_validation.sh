#!/bin/bash
# scripts/rapport_validation.sh

echo "=============================================="
echo "  RAPPORT DE VALIDATION - PROTOTYPE"
echo "  $(date '+%d/%m/%Y %H:%M')"
echo "=============================================="
echo ""

echo "📦 BASE DE DONNÉES"
echo "-------------------"
python3 manage.py shell -c "
from apps.accounts.models import ProfilEtudiant
from apps.academics.models import ResultatAcademique
from apps.alerts.models import Alerte
from apps.analytics.models import IndicateurAcademique
print(f'Étudiants: {ProfilEtudiant.objects.count()}')
print(f'Résultats: {ResultatAcademique.objects.count()}')
print(f'Alertes: {Alerte.objects.count()}')
print(f'Indicateurs: {IndicateurAcademique.objects.count()}')
"
echo ""

echo "🔄 FLUX ETL → KPI → ALERTES"
echo "----------------------------"
python3 manage.py etl_run --source mock 2>&1 | grep -E "import|créé|erreur"
python3 manage.py kpi_compute --all 2>&1 | grep -E "calcul|KPI|fait"
python3 manage.py archiver_alertes 2>&1 | grep -E "archiv|alert"
echo ""

# --- PASSE 1 : PERFORMANCE SEULE ---
echo "⏱ TESTS DE PERFORMANCE"
echo "-----------------------"
PERF_OUTPUT=$(pytest tests_integration/test_performance.py -v -s --tb=short 2>&1)
echo "$PERF_OUTPUT" | grep -E "PASSED|FAILED"
echo "$PERF_OUTPUT" | grep "%LATEXROW%" | sed 's/%LATEXROW% //' > rapport_validation_perf.tex
echo "📄 -> rapport_validation_perf.tex"
echo ""

# --- PASSE 2 : USAGES / FONCTIONNEL + COUVERTURE ---
echo "🔗 TESTS FONCTIONNELS ET COUVERTURE"
echo "-------------------------------------"
pytest --cov=apps --cov=domain --cov-report=term-missing --cov-report=html \
  --ignore=tests_integration/test_performance.py -v --tb=short \
  | tee usage_output.txt | grep -E "PASSED|FAILED|TOTAL|Cover"
echo ""
echo "📄 Rapport HTML couverture -> htmlcov/index.html"
echo ""

echo "=============================================="
echo "  RAPPORT TERMINÉ"
echo "=============================================="