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
contacts              → Contacts importés depuis CRM + mapping
segments              → Segments dynamiques avec filtres JSON
segment_memberships   → Association contacts ↔ segments
templates             → Modèles d'email réutilisables
campaigns             → Campagnes marketing (email, SMS, WhatsApp)
campaign_events       → Tracking (sent, delivered, opened, clicked)
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
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI + sert le frontend buildé
│   │   ├── core/
│   │   │   ├── config.py                    # Pydantic Settings (.env)
│   │   │   ├── database.py                  # Multi-DB + SyncSessionWrapper pour pymssql
│   │   │   ├── security.py                  # PBKDF2 hash + JWT
│   │   │   ├── types.py                     # Types portables (GUID, ArrayField, JSONField)
│   │   │   └── query_helpers.py             # Helpers cross-DB
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py                    # 10 modèles ORM (Python 3.9 compatible — Optional[] pas |)
│   │   ├── schemas/
│   │   │   └── schemas.py                   # Pydantic validation
│   │   ├── services/
│   │   │   ├── contact_service.py           # CRUD contacts + stats (raw SQL pour COUNT)
│   │   │   ├── campaign_service.py          # CRUD campagnes
│   │   │   └── email_service.py             # Envoi SMTP (pas encore connecté)
│   │   └── api/v1/
│   │       ├── router.py                    # Routeur principal
│   │       └── endpoints/
│   │           ├── auth.py                  # Login, register, refresh, me
│   │           ├── contacts.py              # CRUD + stats + search
│   │           ├── campaigns.py             # CRUD + launch
│   │           ├── analytics.py             # Overview, ranking, detail (raw SQL)
│   │           ├── tracking.py              # Pixel ouverture + redirect clic
│   │           ├── templates_segments.py    # Templates + Segments dynamiques
│   │           ├── integrations.py          # Config connexions DB/CRM/SMTP/WhatsApp
│   │           └── mapping.py               # Mapping externe → Orkestra (5 étapes)
│   ├── seed.py                              # Seed données test (local Docker)
│   ├── fix_azure_passwords.py               # Fix PBKDF2 passwords sur Azure
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx                          # SPA complète (~940 lignes)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── render.yaml
├── docker-compose.yml
├── start.sh / stop.sh
├── .gitignore
├── CLAUDE.md                                # ← Ce fichier
└── GUIDE_DE_TEST.md
```

---

## Pages Frontend (App.jsx)

1. **LoginPage** — Auth JWT, pré-rempli admin@opensid.com
2. **DashboardPage** — KPIs (contacts, emails, taux), graphiques Recharts, funnel, campagnes récentes
3. **ContactsPage** — Liste paginée + recherche, avatar initiales, score/stage
4. **CampaignsPage** — Liste + création (modal avec template/segment), bouton Lancer + Détails
5. **SegmentsPage** — Segments dynamiques, clic → détail contacts, création avec filtre (pays, ville, source...)
6. **AnalyticsPage** — Overview filtrable (7j/30j/90j), ranking campagnes
7. **MappingPage** — 5 étapes : connexion DB → tables → mapping auto-suggest → preview → import
8. **IntegrationsPage** — Config DB/CRM/SMTP/WhatsApp/SMS avec test connexion

---

## Décisions techniques importantes

- **Python 3.9 compat** : `Optional[str]` partout, jamais `str | None`. SQLAlchemy Mapped[] évalue au runtime.
- **pymssql sur Render** : pas de driver ODBC → SyncSessionWrapper wraps sync Session to expose async API
- **COUNT queries en raw SQL** : `func.count(Contact.id)` retourne des résultats bizarres avec pymssql + GUID → utiliser `text("SELECT COUNT(*) FROM ...")`
- **Enums en MAJUSCULE** : les valeurs dans la DB doivent être UPPER (ACTIVE, ADMIN, etc.)
- **Tags/custom_fields** : stockés comme string JSON dans SQL Server (NVARCHAR(MAX)), parsés par `_fix_contact()` avant validation Pydantic
- **Single service Render** : FastAPI sert le frontend buildé depuis `frontend_dist/`. Build command compile le React puis copie dans backend.
- **API URL auto-detect** : `window.location.hostname === "localhost"` → localhost:8000, sinon `/api/v1`

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
- ✅ Dashboard avec KPIs réels depuis Azure SQL
- ✅ Page Contacts — 15 contacts importés depuis CRM-Test
- ✅ Page Campagnes — création avec template + segment + détails analytics
- ✅ Page Segments — dynamiques avec filtres, détail cliquable, création depuis le frontend
- ✅ Page Analytics — overview filtrable, ranking campagnes
- ✅ Page Mapping — 5 étapes, import CRM → Orkestra, auto-suggest mapping
- ✅ Page Intégrations — config DB/CRM avec test connexion (pymssql)
- ✅ Single service Render (backend + frontend sur même URL)

---

## Ce qui RESTE À FAIRE

### Priorité HAUTE
1. **Onglet Diffusion** — Nouvelle page dans la sidebar pour configurer :
   - SMTP (host, port, user, password, TLS) — pour envoi email
   - WhatsApp Business API (Meta token, phone number ID)
   - SMS (Twilio/Vonage — API key, numéro)
   - Séparer de la page Intégrations (qui gère les sources de données)

2. **Envoi réel d'emails** — Le bouton "Lancer" sur une campagne doit :
   - Récupérer les contacts du segment cible
   - Appliquer le template avec personnalisation ({{first_name}}, {{company}})
   - Envoyer via SMTP configuré
   - Enregistrer les events (sent, delivered) dans campaign_events
   - Mettre à jour les compteurs de la campagne

3. **Tracking réel** — Les endpoints existent (`/tracking/open`, `/tracking/click`) mais ne sont pas encore testés en production

4. **CI/CD** — GitHub Actions avec pytest :
   - Tests auth, contacts, campagnes, segments, mapping
   - Lint (ruff/flake8)
   - Build frontend vérifié
   - Auto-deploy sur Render si tests passent

### Priorité MOYENNE
5. **Segments — filtres multiples** — Aujourd'hui un segment = un filtre. Permettre : pays = "Ghana" ET secteur = "Tech"
6. **Import CSV** — Upload fichier CSV + mapping visuel (comme le mapping DB)
7. **Éditeur de template email** — Drag-and-drop ou éditeur HTML visuel
8. **Scoring automatique** — Recalcul du lead_score basé sur les events (ouverture +5, clic +10, etc.)
9. **Envoi WhatsApp réel** — Via Meta Business API
10. **RGPD** — Workflow consentement, droit à l'oubli, export données

### Priorité BASSE
11. **Automation workflows** — Exécution des scénarios (welcome series, nurturing, réactivation)
12. **Landing pages / Formulaires** — Création de landing pages avec formulaires d'inscription
13. **Heatmap de clics** — Visualisation des zones cliquées dans un email
14. **Multi-tenant** — Isolation des données par client/organisation
15. **Alembic migrations** — Migrations DB au lieu de create_all

---

## Bugs connus

1. **Tags en string** — Les contacts importés via mapping ont `tags` stocké comme string JSON (`'["imported","crm"]'`). Le `_fix_contact()` dans contact_service.py parse ça avant validation Pydantic. Solution propre : corriger le mapping pour stocker en format natif.

2. **Segments tous à 15** — Les segments créés manuellement via SQL ont `filter_criteria = '{}'` (vide) → comptent tous les contacts. Solution : mettre des vrais filtres ou créer les segments depuis le frontend avec le formulaire.

3. **Azure SQL serverless pause** — Première requête après inactivité peut timeout. La seconde marche.

4. **`regex` deprecation warnings** — FastAPI logs montrent des warnings `regex has been deprecated, please use pattern instead` dans contacts.py et analytics.py. Pas bloquant mais à corriger.

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
- Toujours utiliser `Optional[str]` et jamais `str | None` (Python 3.9 compat).
- Toujours utiliser `text()` pour les COUNT queries SQL (pymssql + GUID issues).
- Le frontend est un seul fichier `App.jsx` (~940 lignes). Toutes les pages sont dedans.
- Sur Render, pymssql est utilisé (pas pyodbc). Toujours tester avec `try: import pymssql` en premier.
- Les enums dans la DB sont en MAJUSCULE (ACTIVE, ADMIN, SENT, etc.).
