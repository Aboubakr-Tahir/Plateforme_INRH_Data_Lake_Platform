### 1. L'Arborescence de Dossiers

Voici une structure claire, professionnelle et intuitive :

```text
Plateforme_INRH_Data_Lake_Platform/
│
├── docker-compose.yml             # Lance PostgreSQL, MinIO et Redis
├── requirements.txt               # pandas, django, celery, minio, psycopg2-binary, etc.
├── README.md                      # Guide pas-à-pas pour lancer le projet
│
├── notebooks/                     # 🧪 BAC À SABLE / BROUILLONS (Son espace de travail libre)
│   ├── 01_explore_vms.ipynb       # Elle ouvre les CSV, teste des filtres Pandas
│   ├── 02_test_quality_rules.ipynb# Elle code ses premières règles de détection
│   └── scratch_test.py            # Fichier temporaire pour tester des bouts de code
│
├── generator/                     # 🎲 Générateur de données simulées INRH
│   ├── generate_all.py            # Script qui crée les CSV avec erreurs
│   └── mock_data/                 # CSV locaux générés (vms.csv, sales.csv, etc.)
│
├── quality_engine/                # 🧠 LE CŒUR DU MÉMOIRE (Python pur & Pandas)
│   ├── __init__.py
│   ├── dimensions/                # Les 4 dimensions DAMA
│   │   ├── completeness.py        # Vérifie les valeurs manquantes
│   │   ├── validity.py            # Vérifie les formats, coordonnées GPS, vitesses
│   │   ├── uniqueness.py          # Vérifie les doublons
│   │   └── consistency.py         # Cohérence Logbook vs Sales, etc.
│   ├── anomaly_detector.py        # Z-Score, IQR, seuils métier
│   └── scoring.py                 # Formule mathématique du score global
│
├── data_pipeline/                 # ⚙️ LE PIPELINE CELERY (Bronze ➔ Silver ➔ Gold)
│   ├── celery_app.py              # Configuration Celery
│   ├── minio_client.py            # Fonctions simples : upload_to_bronze(), read_from_silver()
│   └── tasks.py                   # Tâches Celery : run_quality_pipeline(batch_id)
│
└── web_platform/                  # 🌐 L'INTERFACE DJANGO (Les 2 Dashboards)
    ├── manage.py
    ├── config/                    # Settings Django, URLs principales
    │   ├── settings.py
    │   └── urls.py
    ├── quality_dashboard/         # Dashboard 1 : Gouvernance, alertes et scores
    │   ├── models.py              # Batch, QualityScore, AnomalyLog
    │   ├── views.py
    │   └── templates/
    └── business_dashboard/        # Dashboard 2 : Métier INRH (exploite Gold)
        ├── views.py
        └── templates/
```