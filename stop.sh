#!/bin/bash
# ═══════════════════════════════════════════════════════
# OS Orkestra — Arrêt complet
# Place ce fichier dans : /Users/zack/Documents/GitHub/OS-Orkestra/
# ═══════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS_FILE="$ROOT/.orkestra_pids"

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}   OS Orkestra — Arrêt                    ${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}"
echo ""

# ── Tuer les process sauvegardés ────────────────────────
if [ -f "$PIDS_FILE" ]; then
    while read PID; do
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "  ${GREEN}✓${NC} Process $PID arrêté"
        fi
    done < "$PIDS_FILE"
    rm -f "$PIDS_FILE"
fi

# ── Tuer uvicorn restant ────────────────────────────────
UVICORN_PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)
if [ -n "$UVICORN_PIDS" ]; then
    echo "$UVICORN_PIDS" | xargs kill 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Backend (uvicorn) arrêté"
else
    echo -e "  – Backend déjà arrêté"
fi

# ── Tuer le frontend Vite ───────────────────────────────
VITE_PIDS=$(pgrep -f "vite" 2>/dev/null)
if [ -n "$VITE_PIDS" ]; then
    echo "$VITE_PIDS" | xargs kill 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Frontend (vite) arrêté"
else
    echo -e "  – Frontend déjà arrêté"
fi

# ── Docker SQL Server (optionnel) ───────────────────────
echo ""
CONTAINER=$(docker ps --format '{{.Names}}' | grep -i "mssql\|sqlserver\|sql" | head -1)
if [ -n "$CONTAINER" ]; then
    read -p "  Arrêter aussi Docker SQL Server ($CONTAINER) ? (o/n) : " STOP_DB
    if [[ "$STOP_DB" == "o" || "$STOP_DB" == "O" ]]; then
        docker stop "$CONTAINER"
        echo -e "  ${GREEN}✓${NC} SQL Server arrêté"
    else
        echo -e "  – SQL Server laissé en marche"
    fi
fi

# ── Nettoyage logs ──────────────────────────────────────
rm -f "$ROOT/.backend.log" "$ROOT/.frontend.log"

echo ""
echo -e "${GREEN}${BOLD}  Tout est arrêté.${NC}"
echo ""
