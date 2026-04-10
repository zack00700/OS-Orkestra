#!/bin/bash
# ═══════════════════════════════════════════════════════════
# OS HubLine — Script d'installation Mac + SQL Server
# Par OpenSID
# ═══════════════════════════════════════════════════════════

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}       OS HubLine — Installation Mac              ${NC}"
echo -e "${BLUE}${BOLD}       Marketing Automation by OpenSID             ${NC}"
echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""

# ── Détection du dossier projet ─────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}[1/8] Vérification des prérequis...${NC}"
echo ""

# Python
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} Python $PY_VERSION"
else
    echo -e "  ${RED}✗ Python 3 non trouvé${NC}"
    echo "  → Installe avec : brew install python@3.11"
    exit 1
fi

# Node
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "  ${GREEN}✓${NC} Node.js $NODE_VERSION"
else
    echo -e "  ${YELLOW}⚠ Node.js non trouvé (frontend ne pourra pas tourner)${NC}"
    echo "  → Installe avec : brew install node"
fi

# Docker (pour SQL Server)
if command -v docker &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker installé"
else
    echo -e "  ${RED}✗ Docker non trouvé${NC}"
    echo "  → Installe Docker Desktop : https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Vérifier que le Docker SQL Server tourne
echo ""
echo -e "${CYAN}[2/8] Vérification du Docker SQL Server...${NC}"
echo ""

if docker ps | grep -qi "mssql\|sqlserver\|sql-server" 2>/dev/null; then
    CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep -i "mssql\|sqlserver\|sql" | head -1)
    echo -e "  ${GREEN}✓${NC} Conteneur SQL Server trouvé : ${BOLD}$CONTAINER_NAME${NC}"
else
    echo -e "  ${YELLOW}⚠ Aucun conteneur SQL Server détecté en cours d'exécution.${NC}"
    echo ""
    echo "  Tes conteneurs Docker actuels :"
    docker ps --format "    {{.Names}} ({{.Image}})" 2>/dev/null || echo "    (aucun)"
    echo ""
    read -p "  Le conteneur SQL Server est-il bien lancé ? (o/n) : " CONFIRM
    if [[ "$CONFIRM" != "o" && "$CONFIRM" != "O" ]]; then
        echo ""
        echo "  Lance ton conteneur SQL Server d'abord, puis relance ce script."
        exit 1
    fi
fi

# ── Demander les infos SQL Server ───────────────────────
echo ""
echo -e "${CYAN}[3/8] Configuration SQL Server...${NC}"
echo ""

# Mot de passe SA
echo -e "  ${BOLD}Mot de passe SA de ton SQL Server${NC}"
echo -e "  (celui que tu as défini avec MSSQL_SA_PASSWORD dans Docker)"
echo ""
read -sp "  Mot de passe SA : " SA_PASSWORD
echo ""
echo ""

# Nom de la base
read -p "  Nom de la base à créer [hubline] : " DB_NAME
DB_NAME=${DB_NAME:-hubline}

# Port
read -p "  Port SQL Server [1433] : " DB_PORT
DB_PORT=${DB_PORT:-1433}

# Utilisateur dédié (optionnel)
echo ""
echo -e "  ${BOLD}Créer un utilisateur dédié ?${NC} (recommandé, sinon on utilise SA)"
read -p "  Nom d'utilisateur [hubline_user] : " DB_USER
DB_USER=${DB_USER:-hubline_user}

read -sp "  Mot de passe pour $DB_USER [HubLine2026!] : " DB_USER_PASSWORD
DB_USER_PASSWORD=${DB_USER_PASSWORD:-HubLine2026!}
echo ""

# ── Installer les drivers ODBC pour Mac ─────────────────
echo ""
echo -e "${CYAN}[4/8] Installation des drivers SQL Server pour Mac...${NC}"
echo ""

# unixODBC
if brew list unixodbc &>/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} unixODBC déjà installé"
else
    echo -e "  → Installation de unixODBC..."
    brew install unixodbc
    echo -e "  ${GREEN}✓${NC} unixODBC installé"
fi

# Microsoft ODBC Driver 18
if brew list msodbcsql18 &>/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} ODBC Driver 18 déjà installé"
else
    echo -e "  → Installation du driver ODBC Microsoft 18..."
    brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
    brew update
    HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18
    echo -e "  ${GREEN}✓${NC} ODBC Driver 18 installé"
fi

# sqlcmd
if command -v sqlcmd &>/dev/null || command -v /opt/homebrew/bin/sqlcmd &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} sqlcmd disponible"
    SQLCMD=$(command -v sqlcmd || echo "/opt/homebrew/bin/sqlcmd")
else
    # Essayer le nouveau go-sqlcmd
    if brew list sqlcmd &>/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} sqlcmd (go) disponible"
        SQLCMD="sqlcmd"
    else
        echo -e "  → Installation de sqlcmd..."
        brew install sqlcmd || brew install mssql-tools18
        SQLCMD=$(command -v sqlcmd || echo "/opt/homebrew/opt/mssql-tools18/bin/sqlcmd")
        echo -e "  ${GREEN}✓${NC} sqlcmd installé"
    fi
fi

# ── Créer la base et l'utilisateur ──────────────────────
echo ""
echo -e "${CYAN}[5/8] Création de la base de données '${DB_NAME}'...${NC}"
echo ""

# Tester la connexion
echo -e "  → Test de connexion à SQL Server sur localhost:${DB_PORT}..."

# Construire la commande SQL
SQL_CREATE=$(cat <<EOF
-- Créer la base si elle n'existe pas
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '${DB_NAME}')
BEGIN
    CREATE DATABASE [${DB_NAME}];
    PRINT 'Base ${DB_NAME} créée avec succès.';
END
ELSE
    PRINT 'Base ${DB_NAME} existe déjà.';
GO

USE [${DB_NAME}];
GO

-- Créer le login si nécessaire
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = '${DB_USER}')
BEGIN
    CREATE LOGIN [${DB_USER}] WITH PASSWORD = '${DB_USER_PASSWORD}';
    PRINT 'Login ${DB_USER} créé.';
END
GO

-- Créer l'utilisateur dans la base
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = '${DB_USER}')
BEGIN
    CREATE USER [${DB_USER}] FOR LOGIN [${DB_USER}];
    ALTER ROLE db_owner ADD MEMBER [${DB_USER}];
    PRINT 'Utilisateur ${DB_USER} créé et ajouté comme db_owner.';
END
GO
EOF
)

# Exécuter via sqlcmd
echo "$SQL_CREATE" | $SQLCMD -S "localhost,${DB_PORT}" -U sa -P "$SA_PASSWORD" -C 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Base '${DB_NAME}' prête"
    echo -e "  ${GREEN}✓${NC} Utilisateur '${DB_USER}' créé"
else
    echo -e "  ${YELLOW}⚠ Impossible de se connecter avec sqlcmd.${NC}"
    echo "  Vérifie que le Docker SQL Server tourne et que le mot de passe est correct."
    echo "  Tu peux créer la base manuellement avec Azure Data Studio ou DBeaver."
    echo ""
    echo "  SQL à exécuter :"
    echo "    CREATE DATABASE [${DB_NAME}];"
    echo "    CREATE LOGIN [${DB_USER}] WITH PASSWORD = '${DB_USER_PASSWORD}';"
    echo "    USE [${DB_NAME}]; CREATE USER [${DB_USER}] FOR LOGIN [${DB_USER}];"
    echo "    ALTER ROLE db_owner ADD MEMBER [${DB_USER}];"
    echo ""
    read -p "  Continuer quand même ? (o/n) : " SKIP
    if [[ "$SKIP" != "o" && "$SKIP" != "O" ]]; then
        exit 1
    fi
fi

# ── Configurer le .env ──────────────────────────────────
echo ""
echo -e "${CYAN}[6/8] Configuration du fichier .env...${NC}"
echo ""

ENV_FILE="$SCRIPT_DIR/backend/.env"

# Construire l'URL de connexion SQL Server
# Format: mssql://user:password@host:port/database
DB_URL="mssql://${DB_USER}:${DB_USER_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"

# Réécrire le .env avec la bonne config
cat > "$ENV_FILE" <<EOF
# ═══════════════════════════════════════════════════════
# OS HubLine — Configuration
# Généré par setup.sh le $(date +"%Y-%m-%d %H:%M")
# ═══════════════════════════════════════════════════════

# App
APP_NAME=OS HubLine
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Base de données — SQL Server
DATABASE_URL=${DB_URL}

# Redis (optionnel — pour Celery plus tard)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Azure AD (à configurer plus tard)
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# CRM Dynamics 365 (à configurer plus tard)
DYNAMICS_BASE_URL=
DYNAMICS_CLIENT_ID=
DYNAMICS_CLIENT_SECRET=
DYNAMICS_TENANT_ID=

# CRM Salesforce (à configurer plus tard)
SALESFORCE_BASE_URL=
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=

# WhatsApp (à configurer plus tard)
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# SMTP (à configurer plus tard)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@opensid.com
EOF

echo -e "  ${GREEN}✓${NC} Fichier .env créé : $ENV_FILE"
echo -e "  ${GREEN}✓${NC} DATABASE_URL = mssql://${DB_USER}:***@localhost:${DB_PORT}/${DB_NAME}"

# ── Installer les dépendances Python ────────────────────
echo ""
echo -e "${CYAN}[7/8] Installation des dépendances Python...${NC}"
echo ""

cd "$SCRIPT_DIR/backend"

# Créer le venv s'il n'existe pas
if [ ! -d "venv" ]; then
    echo -e "  → Création de l'environnement virtuel Python..."
    python3 -m venv venv
    echo -e "  ${GREEN}✓${NC} venv créé"
fi

# Activer
source venv/bin/activate
echo -e "  ${GREEN}✓${NC} venv activé"

# Installer les deps
echo -e "  → Installation des packages Python (ça peut prendre 1-2 min)..."
pip install --upgrade pip -q

# Core
pip install fastapi uvicorn[standard] pydantic pydantic-settings -q
echo -e "  ${GREEN}✓${NC} FastAPI installé"

# Database — SQLAlchemy + drivers SQL Server
pip install sqlalchemy[asyncio] -q
pip install aioodbc pyodbc -q
echo -e "  ${GREEN}✓${NC} SQLAlchemy + drivers SQL Server installés"

# Auth
pip install pyjwt passlib[bcrypt] python-multipart -q
echo -e "  ${GREEN}✓${NC} Auth (JWT, bcrypt) installé"

# Utils
pip install httpx email-validator python-dotenv aiosqlite -q
echo -e "  ${GREEN}✓${NC} Utilitaires installés"

# ── Installer le frontend ───────────────────────────────
echo ""
echo -e "${CYAN}[8/8] Installation du frontend...${NC}"
echo ""

cd "$SCRIPT_DIR/frontend"

if command -v npm &>/dev/null; then
    echo -e "  → npm install (ça peut prendre 30 sec)..."
    npm install --silent 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Frontend installé"
else
    echo -e "  ${YELLOW}⚠ npm non disponible, frontend non installé${NC}"
    echo "  → Installe Node.js : brew install node"
fi

# ── Résumé ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}       Installation terminée !                     ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Base de données :${NC} SQL Server localhost:${DB_PORT}/${DB_NAME}"
echo -e "  ${BOLD}Utilisateur DB  :${NC} ${DB_USER}"
echo -e "  ${BOLD}Config          :${NC} backend/.env"
echo ""
echo -e "  ${BOLD}${CYAN}Pour lancer le projet :${NC}"
echo ""
echo -e "  ${BOLD}Terminal 1 — Backend :${NC}"
echo -e "    cd $(pwd)/../backend"
echo -e "    source venv/bin/activate"
echo -e "    uvicorn app.main:app --reload --port 8000"
echo ""
echo -e "  ${BOLD}Terminal 2 — Frontend :${NC}"
echo -e "    cd $(pwd)"
echo -e "    npm run dev"
echo ""
echo -e "  ${BOLD}Accès :${NC}"
echo -e "    Dashboard  → ${BLUE}http://localhost:3000${NC}"
echo -e "    API Docs   → ${BLUE}http://localhost:8000/docs${NC}"
echo -e "    Health     → ${BLUE}http://localhost:8000/health${NC}"
echo ""
echo -e "  ${YELLOW}Astuce :${NC} Lance le backend en premier, puis le frontend."
echo ""

# Demander si on lance maintenant
read -p "  Lancer le backend maintenant ? (o/n) : " LAUNCH
if [[ "$LAUNCH" == "o" || "$LAUNCH" == "O" ]]; then
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    echo ""
    echo -e "  ${GREEN}→ Lancement de OS HubLine...${NC}"
    echo ""
    uvicorn app.main:app --reload --port 8000
fi
