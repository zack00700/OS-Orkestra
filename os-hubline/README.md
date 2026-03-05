# OS HubLine

**Marketing Automation & Campaign Management Platform — by OpenSID**

---

## Installation rapide (Mac + SQL Server)

### Prérequis

- Python 3.11+ (`python3 --version`)
- Docker Desktop avec un conteneur SQL Server qui tourne
- Node.js 18+ (`node --version`) — pour le frontend

### Lancer l'installation

```bash
# 1. Dézipper le projet
cd ~/Desktop
tar -xzf ~/Downloads/os-hubline-complet.tar.gz
cd os-hubline

# 2. Lancer le script d'installation
./setup.sh
```

**Le script fait tout automatiquement :**

1. Vérifie que Python, Node et Docker sont installés
2. Détecte ton conteneur SQL Server
3. Te demande le mot de passe SA et le nom de la base
4. Installe les drivers ODBC Microsoft pour Mac (unixodbc + msodbcsql18)
5. Crée la base `hubline` + un utilisateur dédié dans SQL Server
6. Génère le fichier `.env` avec la bonne connexion
7. Crée l'environnement Python et installe toutes les dépendances
8. Installe les dépendances frontend (npm install)
9. Te propose de lancer le backend directement

### Lancer manuellement (après setup)

```bash
# Terminal 1 — Backend
cd os-hubline/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd os-hubline/frontend
npm run dev
```

### Accès

| Quoi | URL |
|------|-----|
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (Redoc) | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

---

## Structure du projet

```
os-hubline/
│
├── setup.sh                     ← LANCER EN PREMIER — installe tout
│
├── backend/                     ← API Python (FastAPI)
│   ├── .env                     ← Config (créé par setup.sh)
│   ├── .env.example             ← Modèle de config
│   ├── requirements.txt         ← Dépendances Python
│   ├── Dockerfile
│   └── app/
│       ├── main.py              ← Point d'entrée
│       ├── core/
│       │   ├── config.py        ← Configuration centralisée
│       │   ├── database.py      ← Connexion multi-DB (PG, SQL Server, MySQL, SQLite, Oracle)
│       │   ├── types.py         ← Types SQL portables (GUID, JSON, Array)
│       │   ├── query_helpers.py ← Requêtes cross-DB (ILIKE/LIKE, pagination, etc.)
│       │   └── security.py      ← JWT, auth, rôles
│       ├── models/models.py     ← Modèles de données (Contact, Campaign, etc.)
│       ├── schemas/schemas.py   ← Validation API (Pydantic)
│       ├── services/            ← Logique métier
│       ├── api/v1/endpoints/    ← Routes REST (auth, contacts, campagnes, intégrations)
│       ├── integrations/        ← Connecteurs CRM Dynamics, Azure AD, WhatsApp
│       └── tasks/               ← Tâches async (sync, envois)
│
├── frontend/                    ← Dashboard React
│   ├── package.json
│   ├── vite.config.js
│   └── src/App.jsx              ← Dashboard principal
│
└── docker-compose.yml           ← Stack Docker complète (optionnel)
```

---

## Bases de données supportées

Le projet est **agnostique** : un seul code, toutes les bases.
Il suffit de changer `DATABASE_URL` dans `backend/.env`.

| Moteur | DATABASE_URL | Ce qui s'adapte automatiquement |
|--------|-------------|-------------------------------|
| **SQL Server** | `mssql://user:pass@host:1433/db` | UNIQUEIDENTIFIER, NVARCHAR(MAX), OFFSET FETCH, LIKE |
| PostgreSQL | `postgresql://user:pass@host:5432/db` | UUID natif, JSONB, ARRAY, ILIKE, LIMIT/OFFSET |
| MySQL | `mysql://user:pass@host:3306/db` | CHAR(36), JSON, JSON_CONTAINS, LIMIT/OFFSET |
| SQLite | `sqlite:///./fichier.db` | CHAR(36), TEXT+JSON, LOWER()+LIKE, LIMIT/OFFSET |
| Oracle | `oracle://user:pass@host:1521/svc` | RAW(16), CLOB, JSON_VALUE, OFFSET FETCH |

### Ce qui change automatiquement entre les moteurs

| Fonctionnalité | PostgreSQL | SQL Server | MySQL | SQLite |
|---------------|-----------|------------|-------|--------|
| UUID | UUID natif | UNIQUEIDENTIFIER | CHAR(36) | CHAR(36) |
| Tableaux (tags) | ARRAY | NVARCHAR(MAX) JSON | JSON | TEXT JSON |
| Champs JSON | JSONB | NVARCHAR(MAX) | JSON | TEXT |
| Texte long | TEXT | NVARCHAR(MAX) | LONGTEXT | TEXT |
| Recherche texte | ILIKE | LIKE (CI par défaut) | LIKE (CI) | LOWER()+LIKE |
| Pagination | LIMIT/OFFSET | OFFSET FETCH | LIMIT/OFFSET | LIMIT/OFFSET |
| Enums | ENUM natif | VARCHAR | VARCHAR | VARCHAR |
| Limite params | 32 767 | 2 100 | 65 535 | 999 |

---

## API — Endpoints principaux

### Auth
- `POST /api/v1/auth/register` — Créer un compte
- `POST /api/v1/auth/login` — Se connecter (retourne un JWT)
- `GET /api/v1/auth/me` — Profil utilisateur connecté

### Contacts
- `GET /api/v1/contacts/` — Liste paginée + filtres (recherche, statut, segment, pays...)
- `POST /api/v1/contacts/` — Créer un contact
- `PATCH /api/v1/contacts/{id}` — Modifier
- `DELETE /api/v1/contacts/{id}` — Supprimer (RGPD)
- `POST /api/v1/contacts/bulk-import` — Import en masse
- `GET /api/v1/contacts/stats` — Statistiques globales

### Campagnes
- `GET /api/v1/campaigns/` — Liste des campagnes
- `POST /api/v1/campaigns/` — Créer une campagne
- `POST /api/v1/campaigns/{id}/launch` — Lancer
- `POST /api/v1/campaigns/{id}/pause` — Mettre en pause
- `GET /api/v1/campaigns/{id}/analytics` — KPIs détaillés
- `GET /api/v1/campaigns/dashboard` — Stats globales dashboard

### Intégrations
- `GET /api/v1/integrations/test/dynamics` — Tester la connexion Dynamics
- `GET /api/v1/integrations/test/azure-ad` — Tester Azure AD
- `POST /api/v1/integrations/sync/dynamics` — Lancer une sync CRM
- `POST /api/v1/integrations/sync/azure-ad` — Lancer une sync annuaire

---

## Commandes utiles

| Action | Commande |
|--------|----------|
| Lancer le backend | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload` |
| Lancer le frontend | `cd frontend && npm run dev` |
| Doc API interactive | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |
| Vérifier la DB | http://localhost:8000/health |
| Arrêter un serveur | `Ctrl + C` |

---

## En cas de problème

### "pyodbc.OperationalError: ... Can't open lib 'ODBC Driver 18 for SQL Server'"
Le driver ODBC n'est pas installé. Lance :
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

### "Login failed for user"
Vérifie le mot de passe dans `backend/.env` → ligne `DATABASE_URL`.

### "ModuleNotFoundError"
```bash
cd backend && source venv/bin/activate && pip install <module_manquant>
```

### "Port 8000 already in use"
```bash
lsof -i :8000
kill -9 <PID>
```

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| API | FastAPI (Python 3.11) |
| ORM | SQLAlchemy 2.0 (multi-DB) |
| Auth | JWT + bcrypt + RBAC |
| Frontend | React 18 + Vite + Tailwind |
| Charts | Recharts |
| DB | SQL Server / PostgreSQL / MySQL / SQLite / Oracle |

---

© 2026 OpenSID — Tous droits réservés
