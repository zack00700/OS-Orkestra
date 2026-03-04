# 🚀 OS HubLine

**Marketing Automation & Campaign Management Platform**  
*By OpenSID*

---

## Architecture

```
os-hubline/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST API routes
│   │   ├── core/               # Config, security, database
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   ├── integrations/       # CRM, Azure AD, WhatsApp connectors
│   │   ├── tasks/              # Celery async tasks
│   │   └── utils/              # Helpers, validators
│   ├── tests/                  # pytest test suite
│   └── migrations/             # Alembic DB migrations
├── frontend/                   # React Dashboard
└── docs/                       # Documentation
```

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| API Framework | FastAPI (Python 3.11+) |
| Base de données | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| File d'attente | Celery 5 |
| ORM | SQLAlchemy 2.0 |
| Auth | OAuth 2.0 / JWT / MSAL |
| Monitoring | Prometheus + Grafana |
| CI/CD | Docker + GitHub Actions |

## Démarrage rapide

```bash
# 1. Cloner le repo
git clone https://github.com/opensid/os-hubline.git
cd os-hubline

# 2. Environnement
cp backend/.env.example backend/.env

# 3. Docker
docker-compose up -d

# 4. Migrations
cd backend && alembic upgrade head

# 5. Lancer le serveur
uvicorn app.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

## Modules

1. **Connecteur CRM** (Dynamics / Salesforce) — sync bidirectionnelle contacts & leads
2. **Connecteur Azure AD** — annuaire interne, SSO, segmentation collaborateurs
3. **ETL & Qualité** — déduplication, validation emails, scoring data quality
4. **Orchestration Campagnes** — création, planification, triggers, multi-canal
5. **Analytics & Reporting** — KPIs, dashboards, exports

## Licence

Propriétaire — © 2026 OpenSID. Tous droits réservés.
