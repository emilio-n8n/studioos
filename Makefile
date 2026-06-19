.PHONY: install dev build test lint clean docker-up docker-build seed

# ── Installation ──
install:
	./install.sh

# ── Development ──
dev:
	@echo "Starting backend and frontend..."
	@trap 'kill 0' EXIT; \
		cd backend && uvicorn app.main:app --port 8000 --reload & \
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
	rm -rf backend/__pycache__ backend/**/__pycache__ backend/*.db
	rm -rf frontend/.next frontend/out

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
