#!/bin/bash
# ═══════════════════════════════════════════════════════
# OS Orkestra — Démarrage complet
# Place ce fichier dans : /Users/zack/Documents/GitHub/OS-Orkestra/
# ═══════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Dossier racine = là où se trouve ce script
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PIDS_FILE="$ROOT/.orkestra_pids"

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}   OS Orkestra — Démarrage               ${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Racine : $ROOT"
echo ""

# Nettoyer les anciens PIDs
rm -f "$PIDS_FILE"

# ── 1. Docker SQL Server ────────────────────────────────
echo -e "${CYAN}[1/3] Docker SQL Server...${NC}"

CONTAINER=$(docker ps -a --format '{{.Names}}' | grep -i "mssql\|sqlserver\|sql" | head -1)

if [ -n "$CONTAINER" ]; then
    RUNNING=$(docker ps --format '{{.Names}}' | grep -i "mssql\|sqlserver\|sql" | head -1)
    if [ -n "$RUNNING" ]; then
        echo -e "  ${GREEN}✓${NC} SQL Server déjà lancé : $RUNNING"
    else
        echo -e "  → Démarrage du conteneur $CONTAINER..."
        docker start "$CONTAINER"
        echo -e "  ${GREEN}✓${NC} SQL Server démarré : $CONTAINER"
        echo -e "  → Attente (5s)..."
        sleep 5
    fi
else
    echo -e "  ${RED}✗ Aucun conteneur SQL Server trouvé${NC}"
    read -p "  Continuer sans SQL Server ? (o/n) : " SKIP
    if [[ "$SKIP" != "o" ]]; then exit 1; fi
fi

echo ""

# ── 2. Backend Python ───────────────────────────────────
echo -e "${CYAN}[2/3] Backend FastAPI...${NC}"

if [ ! -f "$BACKEND/venv/bin/uvicorn" ]; then
    echo -e "  ${RED}✗ uvicorn non trouvé dans $BACKEND/venv/bin/${NC}"
    echo "  Lance d'abord :"
    echo "    cd $BACKEND"
    echo "    python3 -m venv venv"
    echo "    source venv/bin/activate"
    echo "    pip install -r requirements.txt"
    exit 1
fi

# Lancer uvicorn avec le chemin complet du venv
cd "$BACKEND"
"$BACKEND/venv/bin/uvicorn" app.main:app --reload --port 8000 > "$ROOT/.backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PIDS_FILE"
echo -e "  ${GREEN}✓${NC} Backend lancé (PID: $BACKEND_PID)"
echo -e "    API Docs : ${BOLD}http://localhost:8000/docs${NC}"
echo -e "    Health   : ${BOLD}http://localhost:8000/health${NC}"

echo ""

# ── 3. Frontend React ───────────────────────────────────
echo -e "${CYAN}[3/3] Frontend React...${NC}"

cd "$FRONTEND"

if [ ! -d "$FRONTEND/node_modules" ]; then
    echo -e "  → npm install (première fois)..."
    npm install --silent 2>/dev/null
fi

npm run dev > "$ROOT/.frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PIDS_FILE"
echo -e "  ${GREEN}✓${NC} Frontend lancé (PID: $FRONTEND_PID)"
echo -e "    Dashboard : ${BOLD}http://localhost:3000${NC}"

echo ""

# ── Attente + vérification ──────────────────────────────
echo -e "  → Attente du démarrage (5s)..."
sleep 5

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}   Tout est lancé !                       ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Dashboard${NC}  → http://localhost:3000"
echo -e "  ${BOLD}API Docs${NC}   → http://localhost:8000/docs"
echo -e "  ${BOLD}Health${NC}     → http://localhost:8000/health"
echo ""

if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Backend répond !"
else
    echo -e "  ${RED}⚠ Backend ne répond pas — vérifie les logs :${NC}"
    echo ""
    echo "    tail -20 $ROOT/.backend.log"
    echo ""
    echo -e "  ${CYAN}Dernières lignes du log :${NC}"
    tail -10 "$ROOT/.backend.log" 2>/dev/null
fi

echo ""
echo -e "  Pour tout arrêter : ${BOLD}./stop.sh${NC}"
echo ""
