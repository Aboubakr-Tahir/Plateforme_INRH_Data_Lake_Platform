"""
Client MinIO simplifié pour le Data Lake INRH :
Gère automatiquement les 3 buckets du Medallion Architecture :
- inrh-bronze : fichiers bruts horodatés (CSV / JSON)
- inrh-silver : données nettoyées, validées et enrichies (Parquet)
- inrh-gold   : indicateurs agrégés et KPIs scientifiques (Parquet)
"""