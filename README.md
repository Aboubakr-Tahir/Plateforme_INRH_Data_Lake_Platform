# 🌊 INRH Data Lake Platform
## Système Hybride de Détection d'Anomalies et Scoring de Qualité des Données

> **Mémoire de Master Big Data & Cloud Computing**  
> **Étudiante :** Chaimae Anbi  
> **Cadre :** Institut National de Recherche Halieutique (INRH)

---

## 📌 1. Vue d'Ensemble du Projet

Cette plateforme permet de collecter, surveiller et valoriser 4 flux de données maritimes hétérogènes de l'INRH :
1. **`VMS`** : Balises GPS satellite des navires de pêche (position, vitesse, cap).
2. **`LOGBOOK`** : Carnets de bord déclaratifs remplis par les capitaines (captures par marée).
3. **`SALES`** : Ventes officielles aux enchères dans les halles aux poissons (criées portuaires).
4. **`ENV`** : Mesures océanographiques des bouées côtières (température de surface, salinité, chlorophylle-a).

Le système met en œuvre une **architecture Medallion (Bronze ➔ Silver ➔ Gold)** et évalue chaque arrivage selon les **4 dimensions du standard DAMA International** :
- **Complétude** (taux de valeurs non nulles)
- **Validité** (coordonnées maritimes, vitesses réalistes, prix > 0)
- **Unicité** (absence de doublons)
- **Cohérence** (chronologie des dates, cohérence Logbook vs Ventes)

---

## 🏗️ 2. Architecture Technique

```text
Plateforme_INRH_Data_Lake_Platform/
│
├── docker-compose.yml             # Lance PostgreSQL (5432), MinIO (9000/9001) et Redis (6379)
├── requirements.txt               # Dépendances Python gérées ultra-rapidement avec uv
│
├── notebooks/                     # 🧪 BAC À SABLE / BROUILLONS POUR CHAIMAE
│   ├── 01_exploration_inrh.ipynb  # Notebook guidé pas à pas pour tester les filtres
│   └── scratch_test.py            # Script rapide à exécuter dans le terminal
│
├── generator/                     # 🎲 Générateur de données synthétiques réalistes
│   ├── generate_all.py            # Crée les CSV avec anomalies métier et statistiques
│   └── mock_data/                 # CSV générés (VMS, LOGBOOK, SALES, ENV)
│
├── quality_engine/                # 🧠 LE CŒUR DU MÉMOIRE (Algorithmes en Python & Pandas)
│   ├── dimensions/
│   │   ├── completeness.py        # Calcul du taux de complétude
│   │   ├── validity.py            # Validation coordonnées Maroc et bornes physiques
│   │   ├── uniqueness.py          # Détection de doublons
│   │   └── consistency.py         # Cohérence temporelle et inter-sources
│   ├── anomaly_detector.py        # Détecteur Hybride : Règles métier + IQR / Z-Score
│   └── scoring.py                 # Formule pondérée du score global (0% à 100%)
│
├── data_pipeline/                 # ⚙️ ORCHESTRATION DU DATA LAKE
│   ├── minio_client.py            # Client pour les buckets inrh-bronze, silver, gold
│   ├── celery_app.py              # Configuration Celery & Redis
│   └── tasks.py                   # Tâches de traitement et calcul des métadonnées
│
└── web_platform/                  # 🌐 APPLICATION WEB DJANGO (2 DASHBOARDS)
    ├── quality_dashboard/         # Dashboard 1 : Supervision de la qualité et alertes
    └── business_dashboard/        # Dashboard 2 : Restitution scientifique (Gold layer)
```

---

## ⚡ 3. Guide de Démarrage Rapide (avec `uv`)

### Étape 1 : Créer et activer l'environnement virtuel avec `uv`
```bash
# Création ultra-rapide de l'environnement Python 3.11
uv venv --python 3.11

# Activation
source .venv/bin/activate

# Installation des dépendances
uv pip install -r requirements.txt
```

### Étape 2 : Démarrer l'infrastructure avec Docker
```bash
docker compose up -d
```
* **MinIO Console** (Data Lake) : [http://localhost:9001](http://localhost:9001)  
  *(Identifiants : `inrh_minio_admin` / `inrh_minio_password`)*
* **PostgreSQL** (Métadonnées) : port `5432`
* **Redis** (Broker Celery) : port `6379`

### Étape 3 : Générer les données de simulation INRH
```bash
python generator/generate_all.py
```
*(Génère les 4 fichiers CSV avec anomalies réalistes dans `generator/mock_data/`)*.

### Étape 4 : Exécuter le pipeline de qualité
```bash
python data_pipeline/tasks.py
```
*(Lit le fichier VMS, calcule les 4 dimensions DAMA, détecte les anomalies et produit le score global)*.

### Étape 5 : Lancer la plateforme Web Django
```bash
python web_platform/manage.py migrate
python web_platform/manage.py runserver
```
Ouvrez votre navigateur sur : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 👩‍💻 4. Guide de Travail pour Chaimae (Pas-à-pas)

### A. Où travailler sur les brouillons ?
* Votre espace personnel de test est le dossier **`notebooks/`**.
* Pour tester rapidement vos idées en Python sans rien casser, lancez :
  ```bash
  python notebooks/scratch_test.py
  ```
* Vous pouvez ouvrir le notebook `notebooks/01_exploration_inrh.ipynb` pour afficher des graphiques et manipuler les tableaux Pandas.

### B. Commandes Git quotidiennes
Travaillez toujours sur votre branche `dev-chaimae`.
À la fin de chaque séance de travail :
```bash
# 1. Ajouter vos fichiers modifiés
git add .

# 2. Enregistrer votre progression avec un message clair
git commit -m "Ajout des règles de validation VMS"

# 3. Envoyer votre travail sur GitHub
git push origin dev-chaimae
```
Votre binôme relira votre code sur GitHub et le fusionnera dans la branche `main` !
