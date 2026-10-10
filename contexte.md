# 🌊 Contexte Complet — Plateforme INRH Data Lake Platform

> **Dernière mise à jour** : 10 octobre 2026
> **Branche active** : `main` (code complet de référence)
> **Repo** : `https://github.com/Aboubakr-Tahir/Plateforme_INRH_Data_Lake_Platform.git`

---

## 1. Présentation du Projet

### Sujet de Mémoire
**"Système hybride de détection d'anomalies et de scoring de qualité des données"** — Mémoire de Master Big Data pour **Chaimae Anbi**, encadré par l'INRH (Institut National de Recherche Halieutique, Maroc).

### Objectif
Construire une plateforme Data Lake complète qui :
1. **Ingère** 4 sources de données maritimes marocaines (VMS, SALES, LOGBOOK, ENV)
2. **Évalue la qualité** via les 4 dimensions DAMA International (Complétude, Validité, Unicité, Cohérence)
3. **Détecte les anomalies** par une approche hybride (règles déterministes + méthodes statistiques Z-Score / IQR)
4. **Calcule un score de qualité global pondéré** (0–100%, grades A/B/C/D)
5. **Restitue** les résultats via deux dashboards Django (Gouvernance Qualité + Métier INRH)

### Contraintes Pédagogiques
- Chaimae est **débutante en Data Engineering** → le code doit rester simple, modulaire, bien commenté
- **Stratégie double branche Git** :
  - `main` : Code complet, production-grade, 100% fonctionnel (référence)
  - `dev-chaimae` : Même structure mais avec des blocs `# TODO (Chaimae)` de 3–5 lignes de logique à compléter + tests intégrés auto-exécutables
- Technos volontairement simplifiées : **Python + Pandas** (pas Spark), **MinIO local** (pas AWS S3), **Celery basique** (pas Airflow)

---

## 2. Architecture Technique

### Architecture Medallion (Bronze → Silver → Gold)

```
 [Générateur de données synthétiques]
 (VMS, SALES, ENV, LOGBOOK avec anomalies injectées)
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. BRONZE LAYER (MinIO — bucket: bronze)                    │
│    Stockage brut immuable (CSV/JSON horodatés)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. QUALITY ENGINE (Python pur + Pandas)                      │
│    ├── dimensions/ (4 dimensions DAMA)                        │
│    ├── anomaly_detector.py (Hybride: Déterministe + Stats)   │
│    └── scoring.py (Score global pondéré)                     │
└─────────────┬───────────────────────────────┬───────────────┘
              │ (Données nettoyées)           │ (Scores + Anomalies)
              ▼                               ▼
┌──────────────────────────────┐   ┌──────────────────────────┐
│ 3. SILVER / GOLD (MinIO)     │   │ 4. PostgreSQL            │
│    Silver: Parquet validé    │   │    - BatchMetadata       │
│    Gold: KPIs agrégés        │   │    - QualityScore        │
└──────────────────────────────┘   │    - AnomalyLog          │
                                   └─────────────┬────────────┘
                                                 │
                                                 ▼
                                   ┌──────────────────────────┐
                                   │ 5. Django Dashboards     │
                                   │    - Quality Dashboard   │
                                   │    - Business Dashboard  │
                                   └──────────────────────────┘
```

### Stack Technique

| Composant | Technologie | Rôle |
|:---|:---|:---|
| Data Lake | **MinIO** (elestio/minio:latest) | Stockage objet S3-compatible — buckets bronze/silver/gold |
| Base Métadonnées | **PostgreSQL 15** | Scores qualité, logs anomalies, métadonnées batches |
| Message Broker | **Redis 7** | Broker pour les tâches Celery |
| Moteur de calcul | **Python 3.11 + Pandas + NumPy** | Traitement et analyse des données |
| Orchestration | **Celery** (basique) | Pipeline Bronze → Silver → Gold |
| Interface Web | **Django 5 + Chart.js** | Dashboards de gouvernance et métier |
| Env virtuel | **uv** (installé dans `~/.local/bin/uv`) | Gestionnaire d'environnement Python |

### Docker Compose
Le fichier `docker-compose.yml` lance 3 services :
- **postgres** : `postgres:15-alpine` sur port `5432` (db: `inrh_metadata`, user: `inrh_admin`)
- **minio** : `elestio/minio:latest` sur ports `9000` (API S3) et `9001` (Console Web)
- **redis** : `redis:7-alpine` sur port `6379`

> ⚠️ Note : l'image `minio/minio:latest` a échoué (erreur d'authentification au pull) → remplacée par `elestio/minio:latest`.

---

## 3. Arborescence du Projet

```
Plateforme_INRH_Data_Lake_Platform/
│
├── docker-compose.yml              # Lance PostgreSQL, MinIO et Redis
├── requirements.md                 # Dépendances Python (pandas, django, celery, minio, etc.)
├── README.md                       # Guide du projet
├── .gitignore                      # Exclut .venv, .env, *.docx, plan_global.md, mock_data/*.csv
├── .env / .env.example             # Variables d'environnement
│
├── generator/                      # 🎲 Générateur de données synthétiques
│   ├── generate_all.py             # Script principal — génère 4 CSV avec anomalies injectées
│   └── mock_data/                  # Fichiers CSV générés (exclus du git)
│       ├── logbook_batch_01.csv    # 122 lignes (120 marées + 2 doublons)
│       ├── sales_batch_01.csv      # ~186 lignes (ventes en criée)
│       ├── vms_batch_01.csv        # 1500 lignes (pings GPS satellite)
│       └── env_batch_01.csv        # 400 lignes (relevés océanographiques)
│
├── quality_engine/                 # 🧠 CŒUR DU MÉMOIRE — Moteur de qualité
│   ├── __init__.py
│   ├── dimensions/
│   │   ├── __init__.py
│   │   ├── completeness.py         # ✅ Dimension 1 : Complétude (taux de valeurs non-nulles)
│   │   ├── validity.py             # ✅ Dimension 2 : Validité (ZEE, vitesse, prix, température)
│   │   ├── uniqueness.py           # ✅ Dimension 3 : Unicité (doublons stricts + clés PK/BK)
│   │   └── consistency.py          # ✅ Dimension 4 : Cohérence (chronologie + volumes croisés)
│   ├── scoring.py                  # ✅ Score global pondéré (0.25C + 0.35V + 0.20U + 0.20Co)
│   └── anomaly_detector.py         # ✅ Détection hybride (Déterministe + Z-Score + IQR)
│
├── data_pipeline/                  # ⚙️ Pipeline de données (À IMPLÉMENTER)
│   ├── __init__.py
│   ├── celery_app.py               # Configuration Celery (stub)
│   ├── minio_client.py             # Client MinIO (stub — docstring seulement)
│   └── tasks.py                    # Tâches Celery Bronze→Silver→Gold (stub)
│
└── web_platform/                   # 🌐 Interface Django (À IMPLÉMENTER)
    ├── manage.py
    ├── config/                     # Settings Django, URLs
    ├── quality_dashboard/          # Dashboard 1 : Gouvernance qualité
    ├── business_dashboard/         # Dashboard 2 : Métier INRH
    └── templates/
```

---

## 4. Ce Qui Est Fait (✅ Terminé)

### 4.1 Générateur de Données Synthétiques (`generator/generate_all.py`)

Génère en cascade 4 fichiers CSV réalistes avec des **anomalies volontairement injectées** pour tester le moteur de qualité :

#### Référentiels utilisés :
- **SPECIES** (dictionnaire) : 5 espèces marines marocaines (Sardine PIL, Maquereau MAC, Poulpe OCC, Merlu HKE, Sole SOL). Chaque espèce a un prix moyen (`avg_price`), écart-type (`std_price`), et fourchette de capture réaliste (`min_kg`, `max_kg`). Ces valeurs NE SONT PAS des limites légales de pêche — elles représentent les **fourchettes statistiques réalistes** pour un seul trait de pêche d'un chalutier côtier marocain moyen.
- **BUOYS** (liste) : 4 bouées océanographiques fictives ancrées au large d'Agadir, Dakhla, Tan-Tan et Casablanca avec coordonnées GPS réelles.
- **PORTS** : 6 ports marocains (Agadir, Dakhla, Tan-Tan, Casablanca, Nador, Safi)
- **VESSELS** : 24 identifiants de navires (format `MAR-XXXX-XX`)

#### Anomalies injectées par source :

| Source | Type d'anomalie | Détail | Taux |
|:---|:---|:---|:---|
| **LOGBOOK** | Déterministe | Poids négatif | ~3% |
| | Statistique IQR | Poids × 12 (disproportionné) | ~3% |
| | Géographique | Coordonnées dans l'Atlas (terre ferme) | ~2% |
| | Unicité | 2 doublons stricts injectés à la fin | fixe |
| **SALES** | Déterministe | Prix total négatif | ~3% |
| | Statistique Z-Score | Prix unitaire × 10 (faute de frappe) | ~3% |
| | Croisée (Fraude) | Quantité vendue × 4.5 vs Logbook | ~3% |
| | Temporelle | Vente 3 jours AVANT la marée | ~2% |
| **VMS** | Déterministe | Vitesse 85–135 nœuds (impossible) | ~2.5% |
| | Géographique | Point GPS sur terre ferme | ~2.5% |
| | Complétude | Coordonnées NaN (manquantes) | ~2% |
| **ENV** | Déterministe | Température 85°C (panne capteur) | ~2.5% |
| | Statistique Z-Score | Température 11.5°C (froid anormal) | ~2.5% |
| | Complétude | Salinité NaN | ~2.5% |

### 4.2 Quality Engine — Les 4 Dimensions DAMA

#### Dimension 1 : Complétude (`completeness.py`)
- **Formule** : `(Valeurs non-nulles / Total lignes) × 100` par colonne
- **Score global** : Moyenne arithmétique des scores de toutes les colonnes obligatoires
- Retourne : score, détail par colonne, nombre total de manquants, indices des lignes concernées

#### Dimension 2 : Validité (`validity.py`)
- **Règles par source** :
  - **VMS** : Vitesse dans [0.0, 35.0] nœuds + Coordonnées dans la ZEE marocaine (bounding box + détection terre ferme)
  - **SALES** : Prix total > 0.01 MAD + Quantité > 0.1 kg
  - **LOGBOOK** : Poids > 0.1 kg + Coordonnées maritimes
  - **ENV** : Température surface [10.0, 30.0]°C
- **ZEE marocaine** (Zone Économique Exclusive) : Lat [20.5°N, 36.0°N], Lon [-18.0°W, -1.0°W]
- **Détection terre ferme** : Entre 28°N et 34°N, tout point à l'est de -7.0°W est considéré sur terre (Atlas/intérieur)

#### Dimension 3 : Unicité (`uniqueness.py`)
- **3 niveaux de vérification** :
  1. Doublons stricts (toutes colonnes identiques)
  2. Unicité de la clé primaire (PK) : `vms_id`, `log_id`, `sale_id`, `env_id`
  3. Unicité de la clé métier composite (BK) : ex. `vessel_id + timestamp` pour VMS
- **Formule** : `(Total − Doublons) / Total × 100`
- Référentiel `SOURCE_KEYS` : dictionnaire qui mappe chaque source à sa PK et BK

#### Dimension 4 : Cohérence (`consistency.py`)
- **Règle 1 — Chronologie** : `sale_date >= log_date` (la vente en criée doit être le jour même ou après la marée)
- **Règle 2 — Volume croisé** : Si `quantity_kg (SALES) > 2.0 × weight_kg (LOGBOOK)` pour un même `trip_id + species_code` → alerte fraude/sous-déclaration
- Fonctionne en **jointure inter-tables** (merge Pandas sur `trip_id`)

### 4.3 Scoring Global (`scoring.py`)

**Formule mathématique** :
```
Score Global = (0.25 × Complétude) + (0.35 × Validité) + (0.20 × Unicité) + (0.20 × Cohérence)
```

**Pondérations** :
- Validité a le poids le plus fort (35%) car les coordonnées ZEE et les règles métier sont critiques pour l'INRH
- Complétude (25%), Unicité (20%), Cohérence (20%)
- Les poids sont normalisés pour que leur somme = 1.0

**Grades** :
| Score | Grade | Statut |
|:---|:---|:---|
| ≥ 90% | A (Excellent) | PASSED |
| ≥ 75% | B (Bon) | PASSED |
| ≥ 60% | C (Moyen) | WARNING |
| < 60% | D (Critique) | REJECTED |

### 4.4 Détection d'Anomalies Hybride (`anomaly_detector.py`)

Combine **deux approches complémentaires** :

#### Approche 1 — Déterministe (Règles métier strictes)
Des seuils physiques fixes, codés en dur :
- VMS : Vitesse > 35 nœuds → CRITICAL
- SALES : Prix total ≤ 0 → CRITICAL
- LOGBOOK : Poids ≤ 0 → CRITICAL
- ENV : Température < 10°C ou > 30°C → CRITICAL

#### Approche 2 — Statistique (Data-driven)

| Méthode | Formule | Quand l'utiliser | Sources INRH |
|:---|:---|:---|:---|
| **Z-Score** | `Z = \|x − μ\| / σ` , anomalie si `Z > 3.0` | Distributions **symétriques / gaussiennes** | ENV (température, salinité) |
| **IQR** | `[Q1 − 1.5×IQR, Q3 + 1.5×IQR]` | Distributions **asymétriques** (skewed), résistant aux extrêmes | VMS (vitesse), LOGBOOK (poids), SALES (prix, quantité) |

> **Décision clé** : Pourquoi IQR plutôt que Z-Score pour les données asymétriques ?
> Le Z-Score utilise la **moyenne** (μ), qui est fortement influencée par les valeurs extrêmes.
> L'IQR utilise la **médiane** (Q2) et les quartiles (Q1, Q3), qui sont **robustes** aux outliers.
> Pour des données de pêche (tonnages, prix) dont la distribution est très asymétrique (longue queue à droite),
> l'IQR détecte les anomalies bien plus précisément que le Z-Score.

#### Logique hybride dans `hybrid_anomaly_scan()` :
1. D'abord les règles déterministes (sévérité CRITICAL)
2. Puis les méthodes statistiques sur les lignes non déjà flaggées (sévérité WARNING)
3. Chaque anomalie retourne : `row_index`, `entity_id`, `rule`, `method`, `severity`, `message`

---

## 5. Historique Git

### Branche `main` (code complet de référence)
```
a64a3bb  feat(quality): implement complete hybrid anomaly detector (deterministic + Z-score + IQR)
ce92e6d  feat(quality): implement weighted DAMA global quality scoring formula
31f628f  feat(quality): implement complete DAMA consistency dimension
4a26454  feat(quality): implement complete DAMA uniqueness dimension
21beac3  feat(quality): implement complete DAMA validity dimension
6228d79  feat(quality): implement complete DAMA completeness dimension
6ac72d0  adding synthetic data
17f12db  adding schema data source
...      (commits initiaux : arborescence, docker-compose, README)
```

### Branche `dev-chaimae` (exercices avec TODOs)
```
ead6e66  chore(exercise): add anomaly detector scaffolding with TODOs for Chaimae
1df90f4  chore(exercise): add scoring module scaffolding with TODOs for Chaimae
dc47f44  chore(exercise): add consistency dimension scaffolding with TODOs for Chaimae
52dbbf6  chore(exercise): add uniqueness dimension scaffolding with TODOs for Chaimae
2694fa9  chore(exercise): add validity dimension scaffolding with TODOs for Chaimae
154ab68  chore(exercise): add completeness dimension scaffolding with TODOs for Chaimae
```

### État actuel du working tree (branche `main`)
- **Fichier supprimé** : `requirements.txt` (remplacé par `requirements.md`)
- **Fichiers non suivis** : `contexte.md`, `requirements.md`
- **Push en attente** : Les branches locales ne sont pas synchronisées avec le remote (le push nécessite une authentification GitHub — pas de credential helper configuré, pas de clé SSH)

---

## 6. Ce Qui Reste à Faire (🔲 Prochaines Étapes)

### Étape 3 — Pipeline de Données (`data_pipeline/`)

| Fichier | Statut | Travail à faire |
|:---|:---|:---|
| `minio_client.py` | 🔲 Stub (docstring) | Implémenter : `get_client()`, `ensure_buckets()`, `upload_to_bronze()`, `read_from_bronze()`, `write_to_silver()` |
| `tasks.py` | 🔲 Stub (docstring) | Implémenter : `run_quality_pipeline(batch_id)` — charger CSV depuis Bronze → exécuter les 4 dimensions + scoring + anomaly_detector → écrire Parquet dans Silver → enregistrer scores/anomalies dans PostgreSQL |
| `celery_app.py` | 🔲 Stub minimal | Configurer Celery avec le broker Redis |

**Flux du pipeline** :
```
1. Upload CSV brut → MinIO bucket `bronze` (horodaté)
2. Lire CSV depuis Bronze
3. Exécuter quality_engine :
   - completeness.evaluate_dataset_completeness()
   - validity.evaluate_source_validity()
   - uniqueness.evaluate_source_uniqueness()
   - consistency.evaluate_cross_source_consistency()
   - scoring.compute_global_score()
   - anomaly_detector.hybrid_anomaly_scan()
4. Ajouter colonne quality_flag au DataFrame
5. Écrire DataFrame nettoyé en Parquet → MinIO bucket `silver`
6. INSERT scores + anomalies → PostgreSQL (tables: quality_scores, anomaly_logs)
```

### Étape 4 — Interface Web Django (`web_platform/`)

| Composant | Statut | Travail à faire |
|:---|:---|:---|
| `config/settings.py` | 🔲 À configurer | Connecter PostgreSQL (`inrh_metadata`), configurer `INSTALLED_APPS` |
| `quality_dashboard/models.py` | 🔲 À créer | Modèles Django : `BatchMetadata`, `QualityScore`, `AnomalyLog` |
| `quality_dashboard/views.py` | 🔲 À créer | Vues pour afficher scores, grades, alertes, filtres par source/date |
| `quality_dashboard/templates/` | 🔲 À créer | Templates HTML + Chart.js (jauges, barres, tableaux d'alertes) |
| `business_dashboard/` | 🔲 À créer | Dashboard métier INRH (captures par port, par espèce, tendances) |
| Migrations | 🔲 | `python manage.py makemigrations && migrate` |

### Étape 5 — Couche Gold (agrégation)
- Agrégation Gold : captures totales par port/espèce/mois, température moyenne par zone, KPIs scientifiques
- Écriture dans MinIO bucket `gold` en Parquet

### Étape 6 — Push Git + Finalisation
- Configurer l'authentification GitHub (credential helper ou SSH key)
- Push `main` et `dev-chaimae` vers origin
- Documentation finale + README à jour

---

## 7. Fichiers Clés et Leur Rôle

| Fichier | Chemin | Rôle |
|:---|:---|:---|
| Générateur | `generator/generate_all.py` | Crée les 4 CSV synthétiques avec anomalies |
| Complétude | `quality_engine/dimensions/completeness.py` | Taux de valeurs non-nulles par colonne |
| Validité | `quality_engine/dimensions/validity.py` | Conformité ZEE, vitesse, prix, température |
| Unicité | `quality_engine/dimensions/uniqueness.py` | Détection doublons (stricts + PK + BK) |
| Cohérence | `quality_engine/dimensions/consistency.py` | Chronologie et volumes croisés Logbook↔Sales |
| Scoring | `quality_engine/scoring.py` | Formule pondérée + grades A/B/C/D |
| Anomalies | `quality_engine/anomaly_detector.py` | Hybride : Déterministe + Z-Score + IQR |
| Docker | `docker-compose.yml` | PostgreSQL + MinIO + Redis |
| Dépendances | `requirements.md` | Liste des packages Python |

---

## 8. Concepts Fondamentaux du Mémoire (Rappels Théoriques)

### A. Architecture Medallion (Data Lake)
- **Bronze** : Données brutes immuables, jamais modifiées (CSV/JSON horodatés)
- **Silver** : Données validées, nettoyées, enrichies d'un `quality_flag` (Parquet)
- **Gold** : Indicateurs agrégés prêts pour la restitution (KPIs scientifiques)

### B. Les 4 Dimensions DAMA International
1. **Complétude** : % de valeurs non-nulles dans les colonnes obligatoires
2. **Validité** : Conformité des valeurs au domaine de définition (format, intervalle, règles métier)
3. **Unicité** : Absence de redondance et de doublons (lignes + clés)
4. **Cohérence** : Logique relationnelle et temporelle entre colonnes/tables

### C. Détection d'Anomalies Hybride
- **Déterministe** : Règle fixe en code (`vitesse > 35 → anomalie`)
- **Statistique Z-Score** : `|Z| > 3.0` → valeur extrême (distributions normales)
- **Statistique IQR** : Hors `[Q1 − 1.5×IQR, Q3 + 1.5×IQR]` (distributions asymétriques)

### D. Formule du Score Global
```
Score = 0.25 × Complétude + 0.35 × Validité + 0.20 × Unicité + 0.20 × Cohérence
```

---

## 9. Résumé de l'Avancement

| Phase | Composant | Statut |
|:---|:---|:---|
| Étape 1 | Infrastructure Docker (PostgreSQL, MinIO, Redis) | ✅ Fait |
| Étape 1 | Générateur de données synthétiques | ✅ Fait |
| Étape 2 | Dimension 1 — Complétude | ✅ Fait |
| Étape 2 | Dimension 2 — Validité | ✅ Fait |
| Étape 2 | Dimension 3 — Unicité | ✅ Fait |
| Étape 2 | Dimension 4 — Cohérence | ✅ Fait |
| Étape 2 | Scoring global pondéré | ✅ Fait |
| Étape 2 | Détection anomalies hybride | ✅ Fait |
| Étape 2 | Versions exercice `dev-chaimae` (6 modules) | ✅ Fait |
| **Étape 3** | **Pipeline data_pipeline/ (MinIO + Celery)** | **🔲 À faire** |
| **Étape 4** | **Interface Django (2 dashboards)** | **🔲 À faire** |
| Étape 5 | Couche Gold (agrégation KPIs) | 🔲 À faire |
| Étape 6 | Push Git + Documentation finale | 🔲 À faire (auth GitHub à configurer) |

> **On est actuellement à la fin de l'Étape 2. La prochaine étape est l'Étape 3 : implémenter le pipeline `data_pipeline/` (client MinIO + tâches Celery pour le flux Bronze → Silver → Gold).**
