#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${BLUE}[studioos]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ok  ]${NC} $1"; }
fail() { echo -e "${RED}[fail]${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        StudioOS v3 — Installation    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Pre-flight checks ──
OS="$(uname -s)"
case "$OS" in
  Linux|Darwin) log "OS: $OS" ;;
  *)            log "Warning: untested OS: $OS" ;;
esac

# Python
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    PYTHON="$cmd"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  fail "Python 3 not found. Install Python 3.11+ first."
  exit 1
fi
PYVER=$($PYTHON --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
log "Python $PYVER found"

# Node
if ! command -v node &>/dev/null; then
  fail "Node.js not found. Install Node.js 18+ first."
  exit 1
fi
log "Node.js $(node --version) found"

if ! command -v npm &>/dev/null; then
  fail "npm not found."
  exit 1
fi

# ── Backend ──
echo ""
log "━━━ Installing backend ━━━"
cd backend

# Virtual env
if [ ! -d ".venv" ]; then
  $PYTHON -m venv .venv
  ok "Virtual env created"
fi
source .venv/bin/activate

pip install --quiet --upgrade -r requirements.txt
ok "Python dependencies installed"

# .env
if [ ! -f .env ]; then
  cp .env.example .env 2>/dev/null || true
  ok "Created .env from .env.example"
fi

cd ..

# ── Frontend ──
echo ""
log "━━━ Installing frontend ━━━"
cd frontend

if [ -f package-lock.json ]; then
  npm ci --loglevel=warn
else
  npm install --loglevel=warn
fi
ok "Node dependencies installed"

cd ..

# ── Seed demo project ──
echo ""
log "━━━ Seeding demo project ━━━"
cd backend
source .venv/bin/activate
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from scripts.seed import seed
asyncio.run(seed())
" 2>/dev/null && ok "Demo project seeded with generated website" || log "Seed skipped (run 'make seed' later)"
cd ..

# ── Done ──
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Installation complete!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Start StudioOS:"
echo ""
echo "    make dev"
echo ""
echo "  Or with Docker:"
echo ""
echo "    make docker-up"
echo ""
echo "  Then open: http://localhost:3000"
echo ""
echo "  API key 'demo' works out of the box."
echo ""
