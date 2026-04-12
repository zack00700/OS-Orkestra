# OS Orkestra — CLAUDE.md

> Ce fichier documente le contexte complet du projet pour Claude Code.
> Dernière mise à jour : 12 avril 2026

## Le Projet

**OS Orkestra** est un outil de marketing automation développé par **OpenSID** pour remplacer Oracle Eloqua. Il permet d'importer des contacts depuis des CRM/bases externes, de créer des campagnes email/SMS/WhatsApp, de segmenter les contacts, et d'analyser les performances.

**Développeur** : Zack (dev Python/Data, pas de front — le frontend est géré par Claude)
**Repo** : https://github.com/zack00700/OS-Orkestra
**URL live** : https://os-orkestra.onrender.com
**Login test** : admin@opensid.com / Test1234

---

## Architecture

### Backend
- **Framework** : FastAPI (Python)
- **ORM** : SQLAlchemy 2.0
- **Auth** : JWT (PBKDF2 pour le hashing, pas bcrypt — incompatible Python 3.9)
- **Base interne** : Azure SQL Server `osmdm-server.database.windows.net` / database `Orkestra`
- **Base CRM test** : Azure SQL Server même serveur / database `CRM-Test`
- **Driver SQL Server** : pymssql (pas pyodbc — pas d'ODBC driver sur Render)
- **Mode DB** : Sync wrappé (SyncSessionWrapper simule AsyncSession pour pymssql)
- **Déploiement** : Render (single Web Service — backend sert aussi le frontend buildé)

### Frontend
- **Framework** : React 18 + Vite
- **CSS** : Tailwind CSS
- **Graphiques** : Recharts
- **Icônes** : Lucide React
- **Font** : Outfit (Google Fonts)
- **API URL** : `/api/v1` en prod (Render), `http://localhost:8000/api/v1` en local

### Base de données Orkestra (10 tables)
```
users                 → Comptes admin/manager/editor/viewer
contacts              → Contacts importés depuis CRM + mapping + ajout manuel
segments              → Segments dynamiques avec filtres JSON
segment_memberships   → Association contacts ↔ segments
templates             → Modèles d'email réutilisables
campaigns             → Campagnes marketing (email, SMS, WhatsApp)
campaign_events       → Tracking (sent, delivered, opened, clicked) + scoring
automation_scenarios  → Scénarios d'automatisation (workflow)
sync_logs             → Logs de synchronisation CRM
data_quality_reports  → Rapports qualité des données
```

### Base CRM-Test (3 tables — simule un CRM client)
```
Clients       → 15 contacts de test
Opportunites  → 11 opportunités liées aux clients
Interactions  → 10 interactions commerciales
```

---

## Structure du repo

```
OS-Orkestra/
├── .github/
│   └── workflows/
│       └── ci.yml                               # CI/CD GitHub Actions (lint + tests)
├── backend/
│   ├── app/
│   │   ├── main.py                              # FastAPI + sert le frontend buildé
│   │   ├── core/
│   │   │   ├── config.py                        # Pydantic Settings (.env)
│   │   │   ├── database.py                      # Multi-DB + SyncSessionWrapper pour pymssql
│   │   │   ├── security.py                      # PBKDF2 hash + JWT
│   │   │   ├── types.py                         # Types portables (GUID, ArrayField, JSONField)
│   │   │   └── query_helpers.py                 # Helpers cross-DB (pagination, search, json)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py                        # 10 modèles ORM (Python 3.9 compatible)
│   │   ├── schemas/
│   │   │   ├── __init__.py                      # Imports explicites (pas de wildcard)
│   │   │   └── schemas.py                       # Pydantic validation
│   │   ├── services/
│   │   │   ├── contact_service.py               # CRUD contacts + stats + bulk import
│   │   │   ├── campaign_service.py              # CRUD campagnes
│   │   │   └── email_service.py                 # (legacy — remplacé par diffusion.py)
│   │   ├── tasks/
│   │   │   └── celery_tasks.py                  # Tasks async (WhatsApp — TODO)
│   │   └── api/v1/
│   │       ├── router.py                        # Routeur principal (inclut diffusion)
│   │       └── endpoints/
│   │           ├── auth.py                      # Login, register, refresh, me
│   │           ├── contacts.py                  # CRUD + stats + search + bulk-import + ajout manuel
│   │           ├── campaigns.py                 # CRUD + launch
│   │           ├── analytics.py                 # Overview, ranking, detail (raw SQL)
│   │           ├── tracking.py                  # Pixel ouverture + redirect clic + scoring auto
│   │           ├── templates_segments.py         # Templates + Segments dynamiques
│   │           ├── integrations.py              # Config connexions DB/CRM
│   │           ├── diffusion.py                 # Config SMTP/WhatsApp/SMS + envoi réel campagnes
│   │           └── mapping.py                   # Mapping externe → Orkestra (5 étapes)
│   ├── tests/
│   │   ├── conftest.py                          # SQLite in-memory + StaticPool + fixtures
│   │   ├── test_auth.py                         # 5 tests (login, register, me)
│   │   ├── test_contacts.py                     # 5 tests (CRUD, search, stats)
│   │   ├── test_campaigns.py                    # 3 tests (create, list, unauth)
│   │   ├── test_segments.py                     # 5 tests (create, list, count, contacts, delete)
│   │   ├── test_analytics.py                    # 3 tests (overview, ranking, unauth)
│   │   ��── test_diffusion.py                    # 3 tests (config, smtp, unauth)
│   │   └── test_scoring.py                      # 4 tests (summary, open pixel, click redirect, bad url)
│   ├── pyproject.toml                           # Config pytest + ruff
���   ├── seed.py
│   ├── fix_azure_passwords.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx                              # SPA complète (~940 lignes)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── render.yaml
├── docker-compose.yml
├── start.sh / stop.sh
├── .gitignore
├── CLAUDE.md                                    # ← Ce fichier
└── GUIDE_DE_TEST.md
```

---

## Pages Frontend (App.jsx)

1. **LoginPage** — Auth JWT, pré-rempli admin@opensid.com
2. **DashboardPage** — KPIs (contacts, emails, taux), graphiques Recharts, funnel, campagnes récentes
3. **ContactsPage** — Liste paginée + recherche, avatar initiales, score/stage, ajout manuel
4. **CampaignsPage** — Liste + création (modal avec template/segment), bouton Lancer + Détails
5. **SegmentsPage** — Segments dynamiques, clic → détail contacts, création avec filtre (pays, ville, source...)
6. **AnalyticsPage** — Overview filtrable (7j/30j/90j), ranking campagnes
7. **MappingPage** — 5 étapes : connexion DB → tables → mapping auto-suggest → preview → import
8. **IntegrationsPage** — Config DB/CRM avec test connexion
9. **DiffusionPage** — Config SMTP/WhatsApp/SMS + test connexion + envoi test email

---

## Décisions techniques importantes

- **Python 3.9 compat** : `Optional[str]` partout, jamais `str | None`. `List[X]` jamais `list[X]`. SQLAlchemy Mapped[] évalue au runtime.
- **pymssql sur Render** : pas de driver ODBC → SyncSessionWrapper wraps sync Session to expose async API
- **COUNT queries en raw SQL** : `func.count(Contact.id)` retourne des résultats bizarres avec pymssql + GUID → utiliser `text("SELECT COUNT(*) FROM ...")`
- **Enums en lowercase** : les valeurs dans les Enums Python sont lowercase (`"active"`, `"draft"`, `"opened"`, etc.) — NE PAS utiliser MAJUSCULE dans le code
- **Tags/custom_fields** : stockés comme string JSON dans SQL Server (NVARCHAR(MAX)), parsés par `_fix_contact()` avant validation Pydantic
- **Single service Render** : FastAPI sert le frontend buildé depuis `frontend_dist/`. Build command compile le React puis copie dans backend.
- **API URL auto-detect** : `window.location.hostname === "localhost"` → localhost:8000, sinon `/api/v1`
- **Raw SQL pagination** : toujours utiliser `build_raw_paginated_query()` de `query_helpers.py` (génère LIMIT/OFFSET pour SQLite/PG, OFFSET FETCH pour SQL Server). Ne JAMAIS hardcoder `OFFSET ... ROWS FETCH NEXT`.
- **Schemas __init__.py** : imports explicites, pas de `from ... import *` (ruff F403)
- **Tracking rollback** : les endpoints tracking doivent toujours `await db.rollback()` dans les blocs `except` pour éviter les sessions corrompues (PendingRollbackError)
- **SMTP non-bloquant** : `_send_email_async()` utilise `asyncio.get_event_loop().run_in_executor()` pour ne pas bloquer FastAPI
- **Filtres segments anti-injection** : whitelist `ALLOWED_FILTER_COLUMNS` + paramètres bindés (`:p0`, `:p1`)

---

## CI/CD (GitHub Actions)

Fichier : `.github/workflows/ci.yml`
- **Lint** : `ruff check app/ --ignore E501,F401`
- **Tests** : `pytest tests/ -v --tb=short` (30 tests, SQLite in-memory)
- **Config tests** : `conftest.py` utilise `sqlite+aiosqlite://` avec `StaticPool` (toutes les connexions partagent la même base en RAM)
- **Auto-deploy** : TODO — déclencher deploy Render si tests passent

### Tests actuels (30 tests — tous passent)
```
test_auth.py          → 5 tests (login success/fail, register, me auth/unauth)
test_contacts.py      → 5 tests (create, list, search, stats, unauth)
test_campaigns.py     → 3 tests (create, list, unauth)
test_segments.py      → 5 tests (create, list, dynamic count, contacts, delete)
test_analytics.py     → 3 tests (overview, ranking, unauth)
test_diffusion.py     → 3 tests (get config, configure smtp, unauth)
test_scoring.py       → 4 tests (summary, open pixel, click redirect, bad url reject)
```

---

## Variables d'environnement (Render)

```
DATABASE_URL=mssql+pymssql://mdm-admin:***@osmdm-server.database.windows.net:1433/Orkestra
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=(generated)
SECRET_KEY=(generated)
ALLOWED_ORIGINS=["*"]
```

## Variables d'environnement (local .env)

```
DATABASE_URL=mssql+pyodbc://sa:***@localhost:1433/hubline?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
ENVIRONMENT=development
DEBUG=true
JWT_SECRET_KEY=dev-secret
SECRET_KEY=dev-secret
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

---

## Build Command Render

```
cd ../frontend && npm install && npm run build && cp -r dist ../backend/frontend_dist && cd ../backend && pip install --upgrade pip && pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" pydantic pydantic-settings pyjwt python-multipart httpx email-validator python-dotenv pymssql aiosqlite
```

---

## Ce qui FONCTIONNE (déployé sur Render)

- ✅ Login / JWT auth avec RBAC (admin, manager, editor, viewer)
- ��� Dashboard avec KPIs réels depuis Azure SQL
- ✅ Page Contacts — 15 contacts importés depuis CRM-Test + ajout manuel
- ✅ Page Campagnes — création avec template + segment + détails analytics
- ✅ Page Segments — dynamiques avec filtres, détail cliquable, création depuis le frontend
- ✅ Page Analytics — overview filtrable, ranking campagnes
- ✅ Page Mapping — 5 étapes, import CRM → Orkestra, auto-suggest mapping
- ✅ Page Intégrations — config DB/CRM avec test connexion (pymssql)
- ✅ Page Diffusion — config SMTP/WhatsApp/SMS + test connexion + envoi email test
- ✅ Envoi réel campagnes — via SMTP configuré, avec events (sent/delivered) dans campaign_events
- ✅ Tracking — pixel ouverture + redirect clic + scoring automatique (open +5, click +10, unsub -20)
- ✅ Scoring automatique — lead_score et lead_stage mis à jour en temps réel sur les events
- ✅ CI/CD — GitHub Actions avec ruff lint + 30 pytest (SQLite in-memory)
- ✅ Single service Render (backend + frontend sur même URL)

---

## Ce qui RESTE À FAIRE

### Priorité HAUTE
1. **Envoi WhatsApp réel** — Via Meta Business API (endpoint existe dans diffusion.py, pas encore connecté)
2. **Envoi SMS réel** — Via Twilio/Vonage (endpoint existe, pas encore connecté)
3. **Auto-deploy Render** — GitHub Actions déclenche deploy si tests passent
4. **Persistance config diffusion** — Actuellement en mémoire (`_diffusion_config` dict), perdu au redéploiement. Stocker dans une table DB ou dans les env vars.

### Priorité MOYENNE
5. **Segments — filtres multiples** — Aujourd'hui un segment = un filtre. Permettre : pays = "Ghana" ET secteur = "Tech"
6. **Import CSV** — Upload fichier CSV + mapping visuel (comme le mapping DB)
7. **��diteur de template email** — Drag-and-drop ou éditeur HTML visuel
8. **RGPD** — Workflow consentement, droit à l'oubli, export données
9. **`regex` → `pattern`** — Warnings FastAPI dans contacts.py (sort_by, sort_order). Remplacer `regex=` par `pattern=`.

### Priorité BASSE
10. **Automation workflows** — Exécution des scénarios (welcome series, nurturing, réactivation)
11. **Landing pages / Formulaires** — Création de landing pages avec formulaires d'inscription
12. **Heatmap de clics** — Visualisation des zones cliquées dans un email
13. **Multi-tenant** — Isolation des données par client/organisation
14. **Alembic migrations** — Migrations DB au lieu de create_all

---

## Bugs connus

1. **Tags en string** — Les contacts importés via mapping ont `tags` stocké comme string JSON (`'["imported","crm"]'`). Le `_fix_contact()` dans contact_service.py parse ça avant validation Pydantic. Solution propre : corriger le mapping pour stocker en format natif.

2. **Segments tous à 15** — Les segments créés manuellement via SQL ont `filter_criteria = '{}'` (vide) → comptent tous les contacts. Solution : mettre des vrais filtres ou créer les segments depuis le frontend avec le formulaire.

3. **Azure SQL serverless pause** — Première requête après inactivité peut timeout. La seconde marche.

4. **Config diffusion volatile** — La config SMTP/WhatsApp/SMS est stockée en mémoire. Perdue au redéploiement Render. Solution : persister dans une table DB.

---

## Corrections effectuées le 12 avril 2026

### Session de review/fix avec Claude Code :

**diffusion.py** (nouveau endpoint) :
- Fix SQL Injection dans les filtres de segment → whitelist `ALLOWED_FILTER_COLUMNS` + paramètres bindés
- Comparaison enum status insensible à la casse
- Extraction `_get_segment_contacts()` en helper
- SMTP non-bloquant via `run_in_executor` (`_send_email_async` / `_send_email_sync`)
- `server.quit()` dans un bloc `finally`
- Logs avec `%s` au lieu de f-strings

**tracking.py** (scoring automatique) :
- Fix `_calculate_lead_stage` : retournait MAJUSCULE (`"PURCHASE"`) au lieu de lowercase (`"purchase"`)
- Fix `track_unsubscribe` : status `'UNSUBSCRIBED'` → `'unsubscribed'`
- Remplacé les UPDATE raw SQL par l'ORM (lead_score, lead_stage, status)
- Fix Open Redirect : validation `urlparse` → refuse si pas http/https
- Ajout `await db.rollback()` dans tous les blocs `except` (empêche PendingRollbackError)

**contacts.py** :
- Fix `list[ContactCreate]` → `List[ContactCreate]` (compat Python 3.9)

**templates_segments.py** :
- Fix pagination hardcodée SQL Server (`OFFSET ROWS FETCH`) → `build_raw_paginated_query()` portable
- Fix `Template.is_active == True` → `Template.is_active.is_(True)` (ruff E712)

**conftest.py** (tests) :
- Fix SQLite readonly → `sqlite+aiosqlite://` in-memory + `StaticPool`
- Suppression cleanup fichier `test.db`

**Lint (ruff)** :
- `query_helpers.py` : 6x whitespace dans lignes vides
- `security.py` : newline manquant en fin de fichier
- `types.py` : 2x whitespace dans lignes vides
- `schemas/__init__.py` : `import *` → imports explicites
- `celery_tasks.py` : variable inutilisée `connector` → `_connector`

---

## Comptes de test

| Email | Password | Rôle |
|-------|----------|------|
| admin@opensid.com | Test1234 | admin |
| zack@opensid.com | Test1234 | admin |
| marketing@opensid.com | Test1234 | manager |
| commercial@opensid.com | Test1234 | editor |
| viewer@opensid.com | Test1234 | viewer |

---

## Pour tester en local

```bash
cd /Users/zack/Documents/GitHub/OS-Orkestra
./start.sh
# → Dashboard : http://localhost:3000
# → API Docs : http://localhost:8000/docs
# → Health : http://localhost:8000/health
```

## Pour tester le mapping

1. Page Mapping → Connexion :
   - Host : osmdm-server.database.windows.net
   - Port : 1433
   - User : mdm-admin
   - Password : (ton mdp Azure)
   - Base : CRM-Test
2. Sélectionner la table "Clients"
3. Le mapping auto-suggère les correspondances
4. Prévisualiser → Importer

---

## Notes pour Claude Code

- Zack est dev Python/Data, pas de front. Il faut toujours fournir les fichiers frontend prêts à coller.
- Toujours utiliser `Optional[str]` et jamais `str | None` (Python 3.9 compat). Idem `List[X]` pas `list[X]`.
- Toujours utiliser `text()` pour les COUNT queries SQL (pymssql + GUID issues).
- Toujours utiliser `build_raw_paginated_query()` pour la pagination en raw SQL (portable SQLite/PG/SQL Server).
- Le frontend est un seul fichier `App.jsx` (~940 lignes). Toutes les pages sont dedans.
- Sur Render, pymssql est utilisé (pas pyodbc). Toujours tester avec `try: import pymssql` en premier.
- Les enums dans le code Python sont en **lowercase** (`"active"`, `"draft"`, `"opened"`, `"purchase"`, etc.).
- Les blocs `except` qui catchent des erreurs DB doivent faire `await db.rollback()` pour éviter les sessions corrompues.
- Les tests CI utilisent SQLite in-memory — ne pas écrire de raw SQL spécifique SQL Server dans les endpoints sans passer par les helpers portables.
- Ruff lint : `ruff check app/ --ignore E501,F401`. Pas de `import *`, pas de `== True`, pas de whitespace dans les lignes vides.
