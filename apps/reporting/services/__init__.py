"""Services de génération de rapports (BF08) — PDF, Excel, CSV.

Conformément à la Clean Architecture, toute la logique de génération
de rapports réside ici. Les vues ne font qu'appeler ces services et
renvoyer les fichiers téléchargeables.

Formats supportés :
  - PDF : synthèse académique mise en page (ReportLab)
  - Excel : tableur détaillé des indicateurs par étudiant et UE (openpyxl)
  - CSV  : données brutes séparées par virgule (stdlib)
"""
