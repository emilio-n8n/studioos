# StudioOS v3

**Autonomous Organization System** — Describe a project, and StudioOS builds a complete organization (departments, roles, agents, tasks) and generates a production-ready website.

## Quick Start

### One command

```bash
./install.sh && make dev
```

### Manual

```bash
# Install
./install.sh

# Start (backend + frontend)
make dev
```

Open http://localhost:3000. Use API key `demo` for a no-setup experience.

### Docker

```bash
make docker-up
```

## Architecture

```
studioos/
├── backend/          # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/          # REST + WebSocket endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── kernel/       # EventBus, TaskEngine, MemorySystem
│   │   ├── org_intelligence/  # StrategicPlanner, Recruiter, AgentFactory
│   │   └── workforce/    # AgentExecutor, FileManager
│   └── scripts/seed.py   # Demo data seeder
├── frontend/         # Next.js 16 (App Router)
│   ├── app/              # Pages
│   └── components/       # Dashboard, OrgChart, GenerationPanel
├── docker-compose.yml
├── Makefile
└── install.sh
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make dev` | Start backend + frontend concurrently |
| `make build` | Build frontend for production |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start with Docker Compose |
| `make seed` | Seed demo project + generate website |
| `make clean` | Remove build artifacts |

## Configuration

All configuration is via environment variables (see `backend/.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./studioos.db` | Database connection string |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model for strategic planning |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `OUTPUT_DIR` | `output` | Directory for generated websites |

## How It Works

1. **Describe** your project in natural language
2. **Strategic Planner** (LLM or demo/Rule-based) analyzes and produces: objectives, constraints, risks, complexity, suggested departments
3. **Organization Architect** designs the org structure
4. **Recruiter** & **Agent Factory** define roles and assign agents with tasks
5. **Agent Executor** generates a complete website (HTML/CSS/JS)
6. Preview the generated site directly in the dashboard

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects` | Create project (triggers analysis) |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| GET | `/api/projects/{id}/organization` | Full org structure |
| GET | `/api/projects/{id}/organization/tree` | Org chart tree |
| GET | `/api/projects/{id}/tasks/dashboard` | Dashboard stats |
| PATCH | `/api/projects/{id}/tasks/{tid}/status` | Transition task |
| POST | `/api/projects/{id}/generate` | Generate website |
| GET | `/api/projects/{id}/output` | List generated files |
| WS | `/ws/projects/{id}` | Real-time events |
| GET | `/output/{id}/index.html` | Generated website |

## Deployment

### Production (Docker)

```bash
# Set environment variables
export CORS_ORIGINS=https://yourdomain.com
export ENVIRONMENT=production

# Build and start
make docker-build
make docker-up
```

### Reverse proxy (nginx)

Example nginx config for production:

```nginx
server {
    listen 443 ssl;
    server_name app.mydomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /output/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### Database migrations

For production, use PostgreSQL and Alembic for schema migrations.

## Development

```bash
# Backend (with hot reload)
cd backend && uvicorn app.main:app --port 8000 --reload

# Frontend
cd frontend && npm run dev
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, OpenAI SDK
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, React Flow
- **Infrastructure**: Docker, Docker Compose, GitHub Actions

## License

MIT
