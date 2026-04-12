# OS Orkestra

**Marketing Automation & Campaign Management Platform — by OpenSID**

🔗 **Live** : [https://os-orkestra.onrender.com](https://os-orkestra.onrender.com)

---

## Présentation

OS Orkestra est un outil de marketing automation qui remplace Oracle Eloqua. Il permet de :

- **Importer** des contacts depuis des CRM / bases de données externes (SQL Server, PostgreSQL, MySQL)
- **Segmenter** les contacts par critères dynamiques (pays, secteur, score...)
- **Créer des campagnes** email, SMS et WhatsApp avec templates personnalisables
- **Envoyer** des emails via SMTP avec personnalisation ({{first_name}}, {{company}})
- **Tracker** les ouvertures et clics (pixel tracking + redirection)
- **Analyser** les performances (taux d'ouverture, clic, délivrabilité, rebonds)

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python 3.9+) |
| ORM | SQLAlchemy 2.0 (multi-DB) |
| Auth | JWT + PBKDF2 + RBAC (admin, manager, editor, viewer) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Graphiques | Recharts |
| Base interne | Azure SQL Server (pymssql) |
| Déploiement | Render (single service — backend sert le frontend) |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  OS Orkestra                      │
│              (Render — single service)            │
│                                                   │
│  ┌──────────┐    ┌───────────────────────────┐   │
│  │ React    │    │ FastAPI                    │   │
│  │ Frontend │◄──►│ /api/v1/                   │   │
│  │ (static) │    │ auth, contacts, campaigns  │   │
│  └──────────┘    │ segments, analytics        │   │
│                  │ mapping, diffusion         │   │
│                  │ integrations, tracking     │   │
│                  └─────────┬─────────────────┘   │
│                            │                      │
└────────────────────────────┼──────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Azure SQL      │
                    │  Orkestra (DB)  │
                    │  osmdm-server   │
                    └─────────────────┘
                             ▲
                    ┌────────┴────────┐
                    │  CRM externe    │
                    │  (import via    │
                    │   Mapping)      │
                    └─────────────────┘
```

---

## Pages de l'application

| Page | Description |
|------|-------------|
| **Dashboard** | KPIs temps réel, graphiques performance, funnel, sources |
| **Contacts** | Liste paginée + recherche + ajout manuel |
| **Campagnes** | Création (template + segment), lancement, détails analytics |
| **Segments** | Segments dynamiques avec filtres, détail des contacts, création |
| **Analytics** | Vue d'ensemble filtrable (7j/30j/90j), ranking campagnes |
| **Mapping** | Import CRM en 5 étapes : connexion → table → mapping → preview → import |
| **Diffusion** | Configuration SMTP, WhatsApp, SMS + envoi test + lancement campagnes |
| **Intégrations** | Configuration des sources de données (DB, CRM, Azure AD) |

---

## Déploiement

### Production (Render)

L'application tourne sur Render en single service :
- **URL** : https://os-orkestra.onrender.com
- **Build** : compile le frontend React → copie dans `backend/frontend_dist/` → installe les deps Python
- **Base** : Azure SQL `osmdm-server.database.windows.net` / `Orkestra`

**Build Command** :
```
cd ../frontend && npm install && npm run build && cp -r dist ../backend/frontend_dist && cd ../backend && pip install --upgrade pip && pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" pydantic pydantic-settings pyjwt python-multipart httpx email-validator python-dotenv pymssql aiosqlite
```

**Start Command** :
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Variables d'environnement** :
```
DATABASE_URL=mssql+pymssql://mdm-admin:***@osmdm-server.database.windows.net:1433/Orkestra
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=(generated)
SECRET_KEY=(generated)
ALLOWED_ORIGINS=["*"]
```

### Local (développement)

```bash
# Prérequis : Docker Desktop (SQL Server), Python 3.9+, Node.js 18+
cd OS-Orkestra
./start.sh

# Dashboard : http://localhost:3000
# API Docs  : http://localhost:8000/docs
# Health    : http://localhost:8000/health
```

---

## Structure du projet

```
OS-Orkestra/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI + sert le frontend buildé
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings
│   │   │   ├── database.py              # Multi-DB + SyncSessionWrapper (pymssql)
│   │   │   ├── security.py              # PBKDF2 hash + JWT
│   │   │   ├── types.py                 # Types portables (GUID, JSON, Array)
│   │   │   └── query_helpers.py         # Helpers cross-DB
│   │   ├── models/models.py             # 10 modèles ORM
│   │   ├── schemas/schemas.py           # Validation Pydantic
│   │   ├── services/                    # Logique métier
│   │   └── api/v1/endpoints/            # Tous les endpoints REST
│   ├── seed.py                          # Données de test (local)
│   └── fix_azure_passwords.py           # Fix passwords Azure
├── frontend/
│   ├── src/App.jsx                      # SPA complète (~1100 lignes)
│   ├── package.json
│   └── vite.config.js
├── CLAUDE.md                            # Contexte projet pour Claude Code
├── render.yaml                          # Config Render
├── start.sh / stop.sh                   # Scripts dev local
└── docker-compose.yml                   # Docker (dev local)
```

---

## Bases de données supportées

| Moteur | Driver | Usage |
|--------|--------|-------|
| **SQL Server** | pymssql (Render) / pyodbc (local) | Base interne + CRM externes |
| PostgreSQL | asyncpg | Supporté (non utilisé actuellement) |
| MySQL | aiomysql | Supporté |
| SQLite | aiosqlite | Supporté (dev/test) |

---

## API — Endpoints principaux

### Auth
- `POST /api/v1/auth/login` — Connexion (retourne JWT)
- `POST /api/v1/auth/register` — Créer un compte
- `GET /api/v1/auth/me` — Profil utilisateur

### Contacts
- `GET /api/v1/contacts/` — Liste paginée + recherche
- `POST /api/v1/contacts/` — Créer un contact
- `GET /api/v1/contacts/stats` — Statistiques

### Campagnes
- `GET /api/v1/campaigns/` — Liste
- `POST /api/v1/campaigns/` — Créer

### Segments
- `GET /api/v1/segments/` — Liste (comptage dynamique)
- `GET /api/v1/segments/{id}/contacts` — Contacts du segment
- `POST /api/v1/segments/` — Créer avec filtre

### Analytics
- `GET /api/v1/analytics/overview` — KPIs globaux
- `GET /api/v1/analytics/campaigns/ranking` — Classement
- `GET /api/v1/analytics/campaigns/{id}/detail` — Détail campagne

### Mapping
- `POST /api/v1/mapping/list-tables` — Tables d'une base externe
- `POST /api/v1/mapping/table-schema` — Schéma + auto-suggest
- `POST /api/v1/mapping/preview` — Prévisualiser le mapping
- `POST /api/v1/mapping/import` — Lancer l'import

### Diffusion
- `POST /api/v1/diffusion/config/smtp` — Configurer SMTP
- `POST /api/v1/diffusion/test-smtp` — Tester la connexion
- `POST /api/v1/diffusion/send-test-email` — Envoyer un test
- `POST /api/v1/diffusion/launch-campaign` — Lancer une campagne (envoi réel)

---

## Comptes de test

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| admin@opensid.com | Test1234 | Admin |
| zack@opensid.com | Test1234 | Admin |
| marketing@opensid.com | Test1234 | Manager |
| commercial@opensid.com | Test1234 | Editor |
| viewer@opensid.com | Test1234 | Viewer |

---

## Roadmap

- [x] Import CRM via mapping visuel
- [x] Segments dynamiques
- [x] Création de campagnes
- [x] Envoi réel d'emails (SMTP)
- [x] Page Diffusion (config SMTP/WhatsApp/SMS)
- [x] Ajout manuel de contacts
- [ ] Envoi WhatsApp (Meta Business API)
- [ ] CI/CD GitHub Actions + pytest
- [ ] Scoring automatique basé sur les events
- [ ] Éditeur de template email (drag-and-drop)
- [ ] Automation workflows (scénarios)
- [ ] Write-back CRM (sync bidirectionnelle)
- [ ] Multi-tenant
- [ ] RGPD (consentement, export, droit à l'oubli)

---

© 2026 OpenSID — OS Orkestra
