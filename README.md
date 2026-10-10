# Plateforme INRH Data Lake

Plateforme pédagogique de détection hybride des anomalies et de scoring de
qualité des données scientifiques de l'INRH.

Le projet traite quatre sources synthétiques :

- **VMS** : positions et vitesses des navires ;
- **SALES** : ventes en criée ;
- **LOGBOOK** : déclarations de captures ;
- **ENV** : mesures océanographiques.

## 1. Architecture

```text
Générateur CSV
      ↓
MinIO Bronze (données brutes)
      ↓
Quality Engine
      ├── Complétude
      ├── Validité
      ├── Unicité
      ├── Cohérence
      ├── Score global
      └── Détection hybride
      ↓
MinIO Silver (Parquet + quality_flag)
      ├── PostgreSQL (scores, batches, anomalies)
      └── MinIO Gold (indicateurs agrégés)
                         ↓
                    Dashboards Django
```

## 2. Prérequis

Installer les éléments suivants sur la machine :

- Python **3.11** recommandé ;
- Docker Engine ;
- Docker Compose v2 ;
- Git ;
- `uv` recommandé pour installer les dépendances Python.

Vérifier les installations :

```bash
python3 --version
docker --version
docker compose version
git --version
```

Docker doit être démarré et l'utilisateur doit pouvoir exécuter :

```bash
docker ps
```

Sur Linux, si cette commande demande des droits administrateur, ajouter
l'utilisateur au groupe Docker ou utiliser Docker avec les droits appropriés.

## 3. Récupérer le projet

```bash
git clone https://github.com/Aboubakr-Tahir/Plateforme_INRH_Data_Lake_Platform.git
cd Plateforme_INRH_Data_Lake_Platform
```

Si le projet est déjà présent :

```bash
cd Plateforme_INRH_Data_Lake_Platform
git pull
```

## 4. Créer l'environnement Python

### Option recommandée : `uv`

Installer `uv` si nécessaire :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Créer l'environnement :

```bash
uv venv --python 3.11
```

Activer l'environnement :

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
uv pip install -r requirements.md
```

Le fichier s'appelle `requirements.md`, mais son contenu est au format
requirements pip.

### Alternative avec Python et pip

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.md
```

## 5. Configurer les variables d'environnement

Créer le fichier `.env` à partir du modèle :

```bash
cp .env.example .env
```

La configuration locale attendue est :

```env
DB_NAME=inrh_metadata
DB_USER=inrh_admin
DB_PASSWORD=inrh_password
DB_HOST=localhost
DB_PORT=5432

MINIO_ENDPOINT=localhost:9010
MINIO_ACCESS_KEY=inrh_minio_admin
MINIO_SECRET_KEY=inrh_minio_password
MINIO_SECURE=False

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Le mot de passe indiqué est un mot de passe de développement local. Il doit
être changé pour un environnement partagé ou de production.

## 6. Démarrer toute la plateforme avec une seule commande

Le lanceur [main.py](./main.py) démarre :

- PostgreSQL ;
- Redis ;
- MinIO ;
- le worker Celery ;
- le serveur Django.

Depuis la racine du projet :

```bash
source .venv/bin/activate
python main.py
```

Le dashboard est alors disponible à :

```text
http://127.0.0.1:8000/
```

Pour ouvrir automatiquement le navigateur :

```bash
python main.py --open-browser
```

Pour utiliser un autre port si `8000` est déjà occupé :

```bash
python main.py --port 8001
```

Dans ce cas, ouvrir :

```text
http://127.0.0.1:8001/
```

Le terminal doit afficher notamment :

```text
PostgreSQL, Redis et MinIO sont prêts.
Dashboard disponible sur http://127.0.0.1:8000/
celery@... ready.
```

Ne fermez pas ce terminal pendant l'utilisation de la plateforme.

## 7. Lancer un pipeline depuis Django

1. Ouvrir `http://127.0.0.1:8000/`.
2. Cliquer sur **Lancer un nouveau pipeline**.
3. Attendre l'affichage des états :

```text
GENERATING
INGESTING
PROCESSING
COMPLETED
```

Le bouton exécute le flux complet :

```text
Génération des CSV
    ↓
Upload MinIO Bronze
    ↓
Contrôles Quality Engine
    ↓
Parquet Silver
    ↓
Scores et anomalies PostgreSQL
    ↓
Agrégations Gold
```

L'état, le nombre de sources traitées, les scores et les anomalies sont
actualisés automatiquement dans le navigateur.

Le dashboard qualité est disponible à :

```text
http://127.0.0.1:8000/
```

Le dashboard métier est disponible à :

```text
http://127.0.0.1:8000/business/
```

## 8. Accès aux services

### MinIO

Console web :

```text
http://localhost:9011
```

API utilisée par Python :

```text
localhost:9010
```

Buckets :

```text
bronze
silver
gold
```

Identifiants locaux par défaut :

```text
Utilisateur : inrh_minio_admin
Mot de passe : inrh_minio_password
```

### PostgreSQL

Connexion :

```text
Host     : localhost
Port     : 5432
Database : inrh_metadata
User     : inrh_admin
Password : inrh_password
```

Ouvrir le shell SQL :

```bash
docker exec -it inrh_postgres psql \
  -U inrh_admin \
  -d inrh_metadata
```

Commandes utiles dans `psql` :

```sql
\dt
\d batch_metadata
\d quality_scores
\d anomaly_logs

SELECT * FROM batch_metadata;
SELECT * FROM quality_scores;
SELECT * FROM anomaly_logs LIMIT 20;
\q
```

### Redis

Redis est utilisé comme broker Celery :

```text
localhost:6379
```

Tester Redis :

```bash
docker exec inrh_redis redis-cli ping
```

Résultat attendu :

```text
PONG
```

## 9. Fichiers produits

Après l'exécution d'un batch, les objets sont organisés par identifiant.

### Bronze

```text
bronze/vms/<batch_id>/vms_batch_01.csv
bronze/sales/<batch_id>/sales_batch_01.csv
bronze/logbook/<batch_id>/logbook_batch_01.csv
bronze/env/<batch_id>/env_batch_01.csv
```

### Silver

```text
silver/vms/<batch_id>/vms_<batch_id>.parquet
silver/sales/<batch_id>/sales_<batch_id>.parquet
silver/logbook/<batch_id>/logbook_<batch_id>.parquet
silver/env/<batch_id>/env_<batch_id>.parquet
```

Les fichiers Silver contiennent la colonne `quality_flag` :

```text
VALID
WARNING
CRITICAL
```

### Gold

```text
gold/<batch_id>/sales_by_port_species.parquet
gold/<batch_id>/catches_by_species.parquet
gold/<batch_id>/environment_by_sensor.parquet
gold/<batch_id>/quality_kpis.parquet
```

### PostgreSQL

Les tables de gouvernance sont :

```text
batch_metadata
quality_scores
anomaly_logs
```

## 10. Tests manuels

Activer l'environnement puis exécuter les tests depuis la racine :

```bash
source .venv/bin/activate
python -m notebooks.test_quality_pipeline
python -m notebooks.test_gold_pipeline
```

Le test Celery nécessite qu'un worker soit déjà démarré. Avec `main.py`, il
est démarré automatiquement. Sinon :

```bash
PYTHONPATH=. python -m celery \
  -A data_pipeline.celery_app \
  worker \
  --loglevel=info \
  --pool=solo
```

Puis, dans un autre terminal :

```bash
PYTHONPATH=. python -m notebooks.test_celery_pipeline
```

## 11. Arrêter la plateforme

Dans le terminal où `main.py` tourne :

```text
Ctrl+C
```

Cela arrête le worker Celery et Django, mais conserve les conteneurs Docker et
les données.

Pour arrêter également PostgreSQL, Redis et MinIO :

```bash
docker compose down
```

Pour supprimer aussi les volumes et donc les données locales :

```bash
docker compose down -v
```

Cette dernière commande est destructive pour les données Docker locales.

## 12. Dépannage

### Le dashboard reste sur `QUEUED`

Le worker Celery n'est probablement pas démarré. Utiliser le lanceur :

```bash
python main.py
```

ou démarrer manuellement :

```bash
PYTHONPATH=. python -m celery \
  -A data_pipeline.celery_app \
  worker \
  --loglevel=info \
  --pool=solo
```

Le message suivant doit apparaître :

```text
celery@... ready.
```

### Le port 8000 est déjà utilisé

```bash
python main.py --port 8001
```

### Le port MinIO 9000 est déjà utilisé

Le projet publie volontairement MinIO sur :

```text
9010 → API MinIO interne 9000
9011 → Console MinIO interne 9001
```

Ne pas remplacer `MINIO_ENDPOINT=localhost:9010` par `localhost:9000`.

### Les conteneurs ne démarrent pas

```bash
docker compose ps
docker compose logs --tail=100 postgres
docker compose logs --tail=100 minio
docker compose logs --tail=100 redis
```

Puis relancer :

```bash
docker compose up -d --wait
```

### Django affiche une erreur de dépendance

Vérifier que l'environnement est activé :

```bash
source .venv/bin/activate
which python
```

Puis réinstaller :

```bash
uv pip install -r requirements.md
```

## 13. Structure principale

```text
main.py                       # Lance toute la plateforme
docker-compose.yml            # PostgreSQL, MinIO et Redis
requirements.md               # Dépendances Python
generator/                    # Générateur des quatre CSV
quality_engine/               # Qualité DAMA et anomalies hybrides
data_pipeline/                # MinIO, Celery, pipeline Bronze-Silver-Gold
web_platform/                 # Dashboards Django
notebooks/                    # Scripts et tests d'intégration
```
