# 📚 Bibliothèque personnelle — TP Conteneurisation & Orchestration

Application web en microservices permettant à chaque utilisateur de gérer sa
bibliothèque personnelle (livres à lire, en cours, lus), conteneurisée avec
Docker, orchestrée avec Kubernetes et livrée par un pipeline CI/CD GitHub Actions.

Auteure : Olivia Trask

---

## 1. Architecture

```
                 Navigateur
                     │  http://localhost:3000 (Compose) / :8080 (Kubernetes)
                     ▼
            ┌──────────────────┐
            │   front (Nginx)  │  page web + reverse proxy
            └───┬──────────┬───┘
     /api/auth/ │          │ /api/books/
                ▼          ▼
     ┌──────────────┐  ┌──────────────┐
     │ auth :4001   │  │ books :4002  │   FastAPI (Python 3.13)
     │ inscription, │  │ CRUD livres, │
     │ connexion,   │  │ vérifie le   │
     │ émet le JWT  │  │ JWT          │
     └──────┬───────┘  └──────┬───────┘
            │   table users    │  table user_books
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ PostgreSQL 16    │  volume persistant
            └──────────────────┘
```

| Service | Rôle | Technologie | Port |
|---|---|---|---|
| `front` | Interface web, reverse proxy vers les API | Nginx (non-root) | 8080 |
| `auth` | Inscription, connexion, émission du jeton JWT | FastAPI, bcrypt, PyJWT | 4001 |
| `books` | Ajout, liste, changement de statut des livres de l'utilisateur connecté | FastAPI | 4002 |
| `postgres` | Stockage des données | PostgreSQL 16 | 5432 |

**Communication entre services** : `auth` signe un jeton JWT avec une clé secrète
partagée (`JWT_SECRET`). `books` vérifie ce jeton sans appeler `auth` : les deux
services restent indépendants.

### Endpoints

| Méthode | Route | Service | Auth |
|---|---|---|---|
| GET | `/health` | tous | non |
| POST | `/users/signup` | auth | non |
| POST | `/users/login` | auth | non |
| GET | `/books?status=lu` | books | JWT |
| POST | `/books` | books | JWT |
| PATCH | `/books/{id}/status` | books | JWT |

Documentation interactive (Swagger) en dev : http://localhost:4001/docs et http://localhost:4002/docs

---

## 2. Structure du dépôt

```
.
├── services/
│   ├── auth/      Dockerfile, .dockerignore, requirements.txt, app/
│   ├── books/     Dockerfile, .dockerignore, requirements.txt, app/
│   └── front/     Dockerfile, .dockerignore, nginx.conf, index.html
├── deploy/        manifestes Kubernetes + kustomization.yaml + init.sql
├── .github/workflows/ci-cd.yml
├── docker-compose.yml
├── .env.example   modèle de configuration (le vrai .env n'est pas versionné)
└── .gitignore
```

**Branches** : `main` (protégée, production) ← Pull Request ← `develop` (intégration) ← `feature/*`.

---

## 3. Lancer en développement (Docker Compose)

Prérequis : Docker Desktop.

```bash
cp .env.example .env          # puis modifier les mots de passe dans .env
docker compose up --build     # construit les 3 images et lance les 4 conteneurs
```

- Application : http://localhost:3000
- Arrêter : `docker compose down` (ajouter `-v` pour effacer aussi les données)

La base est créée automatiquement au premier démarrage par `deploy/init.sql`.

---

## 4. Déployer sur Kubernetes (Docker Desktop)

```bash
# 1. Construire les images (tag "dev")
docker compose build

# 2. Créer le namespace et le Secret (jamais stocké dans Git)
kubectl apply -f deploy/namespace.yaml
kubectl create secret generic bibliotheque-secrets -n bibliotheque \
  --from-literal=DB_USER=biblio_user \
  --from-literal=DB_PASSWORD='un-mot-de-passe' \
  --from-literal=JWT_SECRET='une-longue-chaine-aleatoire'

# 3. Déployer toute l'application
kubectl apply -k deploy/

# 4. Suivre le démarrage
kubectl get pods -n bibliotheque -w

# 5. Accéder à l'application -> http://localhost:8080
kubectl port-forward -n bibliotheque svc/front 8080:80
```

### Démonstrations utiles

```bash
# Auto-réparation : supprimer un pod, Kubernetes le recrée
kubectl delete pod -n bibliotheque -l app=books
kubectl get pods -n bibliotheque -w

# Mise à l'échelle
kubectl scale deployment books -n bibliotheque --replicas=4

# Persistance : redémarrer la base, les données restent (PV/PVC)
kubectl rollout restart deployment postgres -n bibliotheque

# Mise à jour sans interruption (rolling update)
kubectl rollout restart deployment auth -n bibliotheque
kubectl rollout status deployment auth -n bibliotheque

# Tout supprimer
kubectl delete namespace bibliotheque && kubectl delete pv postgres-pv
```

**Si les pods restent en `ErrImagePull`** : le cluster ne voit pas les images
construites en local. Utiliser les images publiées par le pipeline : dans
`deploy/kustomization.yaml`, remplacer `newTag: dev` par la version publiée
(ex. `v1.0.0`) et rendre les paquets publics sur GitHub (onglet *Packages* →
*Package settings* → *Change visibility*).

---

## 5. Pipeline CI/CD (GitHub Actions)

Fichier : `.github/workflows/ci-cd.yml`

| Déclencheur | Jobs |
|---|---|
| push sur `develop`, Pull Request | **test** : build des 3 images, lancement de l'appli avec Compose, test de bout en bout (inscription → connexion → ajout de livre → liste → refus sans jeton) |
| tag `v*` posé sur `main` | **test** → **build-and-push** (images taguées `vX.Y.Z` et `latest` sur GHCR) → **deploy** (`kubectl apply -k deploy/`, attente des rollouts, test de fumée) |

Livrer une version :

```bash
# après avoir fusionné develop dans main via une Pull Request
git checkout main && git pull
git tag v1.0.0
git push origin v1.0.0
```

Le cluster Docker Desktop n'étant pas accessible depuis Internet, le job
`deploy` crée un cluster Kubernetes éphémère (kind) dans le runner GitHub et y
applique les manifestes. Pour un vrai cluster distant, il suffirait de
remplacer cette étape par un kubeconfig stocké dans les secrets GitHub.

Secrets GitHub optionnels (Settings → Secrets and variables → Actions) :
`DB_PASSWORD`, `JWT_SECRET`. Sans eux, des valeurs aléatoires sont générées.

---

## 6. Sécurité et gestion des secrets

- Aucun secret dans Git : `.env` et `deploy/secret.yaml` sont dans `.gitignore`,
  seuls des modèles (`.env.example`, `deploy/secret.example.yaml`) sont versionnés.
- Aucun secret dans les images : `.dockerignore` exclut `.env`, les secrets sont
  injectés au démarrage par variables d'environnement.
- Configuration séparée : ConfigMap (hôte, port, nom de base) / Secret
  (utilisateur, mot de passe, clé JWT).
- Mots de passe hachés avec bcrypt, jetons JWT expirant au bout de 60 minutes.
- Conteneurs exécutés sans les droits root (`USER 10001`, `runAsNonRoot`).

---

## 7. Choix techniques

- **Multi-stage build** : l'étape `builder` installe les dépendances dans un
  venv, l'image finale ne copie que ce venv et le code (pas de pip ni de cache).
- **Image `python:3.13-slim`** plutôt qu'alpine : les paquets Python (bcrypt…)
  ont des binaires précompilés pour Debian, ce qui évite de compiler.
- **Driver `pg8000`** : 100 % Python, aucune bibliothèque système à installer.
- **Reverse proxy Nginx** : un seul point d'entrée, pas de CORS, les API ne sont
  pas exposées hors du cluster (Services `ClusterIP`).
- **Probes** : `readinessProbe` (le pod ne reçoit du trafic que s'il est prêt) et
  `livenessProbe` (redémarrage automatique si le service ne répond plus).
- **RollingUpdate** `maxUnavailable: 0` : mises à jour sans interruption.
- **PostgreSQL en `Recreate`** : jamais deux instances sur le même volume.
- **Kustomize** (intégré à `kubectl`) : un seul `kubectl apply -k`, ConfigMap SQL
  générée depuis le même `init.sql` que Docker Compose, tags d'images centralisés.

### Limites et améliorations possibles

- Une seule base partagée par les deux services (idéalement, une base par service).
- PostgreSQL en `Deployment` : en production, on utiliserait un `StatefulSet`
  ou une base managée.
- Volume `hostPath` : adapté à un cluster local à un nœud uniquement.
- Versions des dépendances Python non figées dans `requirements.txt`.
- Pas encore d'Ingress, de HTTPS ni de monitoring.

---

## 8. Utilisation de l'IA

Conformément aux règles du TP :

- **Claude (Anthropic)** a été utilisé pour m'accompagner pas à pas dans la mise
  en place du dépôt et de l'environnement, puis pour générer une première version
  des Dockerfiles, du `docker-compose.yml`, des manifestes Kubernetes, du
  pipeline GitHub Actions et de ce README, ainsi que pour adapter la configuration
  des services (variables d'environnement, reverse proxy).
- Le code des microservices `auth` et `books` et la page web ont été écrits par
  moi, avec l'aide de l'IA pour certaines explications.
- Tout le code généré a été relu, testé sur mon poste (Docker Compose et
  Kubernetes Docker Desktop) et adapté à mon architecture.
- - J'ai identifié et corrigé un problème de healthcheck du front (localhost résolu en IPv6 alors que Nginx écoutait en IPv4), dans la branche fix/front-healthcheck.
