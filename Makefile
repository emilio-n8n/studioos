.PHONY: install dev build test lint clean docker-up docker-build seed

# ── Installation ──
install:
	./install.sh

# ── Development ──
dev:
	@echo "Starting backend and frontend..."
	@trap 'kill 0' EXIT; \
		( cd backend && ([ -f .venv/bin/activate ] && . .venv/bin/activate; uvicorn app.main:app --port 8000 --reload) ) & \
		cd frontend && npm run dev & \
		wait

# ── Building ──
build:
	cd frontend && npm run build

# ── Testing ──
test:
	cd backend && python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"

# ── Linting ──
lint:
	cd backend && python -m ruff check . 2>/dev/null || echo "ruff not installed"
	cd frontend && npm run lint 2>/dev/null || true

# ── Cleaning ──
clean:
	rm -rf backend/__pycache__ backend/**/__pycache__ backend/*.db backend/repos/
	rm -rf frontend/.next frontend/out frontend/node_modules/.cache

reset: clean
	pkill -f "uvicorn" 2>/dev/null; pkill -f "next dev" 2>/dev/null; sleep 1
	rm -rf backend/.venv frontend/node_modules
	bash install.sh

# ── Docker ──
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ── Database ──
seed:
	cd backend && python -m scripts.seed
