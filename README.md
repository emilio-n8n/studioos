# StudioOS

**AI-Native Operating System for Building Organizations**

Describe a project in natural language. StudioOS analyzes it, designs a complete organization (departments, roles, agents, tasks), runs the agents through a production pipeline with review and version control, and delivers the result — all traceable in a real-time dashboard.

→ You don't prompt an AI. You build a company of AI agents.

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
│   │   ├── models/       # SQLAlchemy models (Project, Organization, MemoryNode, Review, PullRequest...)
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── kernel/       # EventBus, EventStore, DAGEngine, GitManager, MemorySystem, TaskEngine
│   │   ├── org_intelligence/  # StrategicPlanner, Recruiter, AgentFactory
│   │   └── workforce/    # AgentExecutor, FileManager
│   └── scripts/seed.py   # Demo data seeder
├── frontend/         # Next.js 16 (App Router)
│   ├── app/              # Pages (Home, Project)
│   └── components/       # Dashboard, OrgChart, MemoryGraph, ReviewPanel, GitPanel
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

### Frontend (API URL)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Auto-detected | Backend API URL (see Codespaces section below) |

The frontend auto-detects the backend URL in order of priority:

1. `NEXT_PUBLIC_API_URL` environment variable (explicit override)
2. GitHub Codespaces: constructed from the forwarded port URL
3. `http://localhost:8000` (local development)

WebSocket URL (`WS_BASE`) is derived automatically from the API URL.

## GitHub Codespaces

StudioOS runs in GitHub Codespaces with zero configuration.

### Quick start

1. Open the repository in Codespaces
2. Wait for the `postCreateCommand` to finish (runs `install.sh`)
3. In the terminal, start both services:

```bash
make dev
```

4. When prompted by VS Code, click **Open in Browser** for port 3000 (frontend).

Or manually open the **Ports** tab and click the globe icon next to port 3000.

### How it works

The frontend automatically detects it is running in Codespaces by inspecting the browser's URL (`*.preview.app.github.dev`). It constructs the correct backend URL to match the forwarded port 8000 — no manual configuration needed.

If behind a custom domain or proxy, set the environment variable explicitly:

```bash
# From the Codespaces terminal
echo "NEXT_PUBLIC_API_URL=https://your-custom-url" >> frontend/.env.local
```

### Troubleshooting

**Frontend cannot reach backend (ERR_CONNECTION_REFUSED)**

The most common cause is the backend not running. Ensure both services are started:

```bash
# In one terminal
cd backend && uvicorn app.main:app --port 8000 --reload

# In another terminal
cd frontend && npm run dev
```

If the issue persists, check the **Ports** tab — make sure ports 3000 and 8000 are both forwarded and set to **Public** if you need access from outside the Codespace.

## How It Works

1. **Describe** your project in natural language
2. **Strategic Planner** (LLM or demo/Rule-based) analyzes and produces: objectives, constraints, risks, complexity, suggested departments — all stored as **Strategic Decisions**
3. **Organization Architect** designs the org structure (departments, hierarchy)
4. **Recruiter** & **Agent Factory** define roles (with summary, permissions, metrics, skills) and assign agents with initial tasks
5. Agents execute tasks and **commit work to git** on their own branches (`agent/{name}`)
6. **Review Layer** — worker submits output, reviewer approves or requests changes, lead merges. No task can reach final status without an approved review (review gate)
7. **Memory Graph** — all decisions, constraints, and artifacts are versioned and shared across every agent. Immutable: new versions append, values never mutate
8. **Event-Sourced Kernel** — every action emits a typed event persisted in an append-only event log, replayable for full traceability
9. **DAG Execution** — tasks with dependencies are topologically sorted and executed in parallel batches
10. Preview results (generated site, git log, PRs) directly in the dashboard

## Event System (V8 Kernel)

Every mutation emits a typed event persisted in the `event_log` table:

| Event | Trigger |
|-------|---------|
| PROJECT_CREATED | Project created via API |
| STRATEGY_GENERATED | Analysis completed |
| ORG_CREATED | Organization designed |
| AGENT_SPAWNED | Agents generated |
| TASK_ASSIGNED / TASK_STARTED / TASK_COMPLETED | Task lifecycle |
| REVIEW_REQUESTED / REVIEW_APPROVED / REVIEW_CHANGES_REQUESTED | Review lifecycle |
| GIT_COMMIT_CREATED / PR_CREATED / PR_MERGED | Git lifecycle |
| MEMORY_CREATED | Memory node created |

Events are replayable via `EventStore.replay()` and the `event_log` table is the single source of truth for the system's complete history.

## DAG Execution

Tasks with `depends_on` dependencies are automatically topologically sorted. The `DAG` engine:
- Validates acyclic constraints
- Returns ready tasks for each parallel execution batch
- Prevents execution of tasks with unmet dependencies

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects` | Create project (triggers analysis) |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| GET | `/api/projects/{id}/organization` | Full org structure |
| GET | `/api/projects/{id}/organization/tree` | Org chart tree |
| GET | `/api/projects/{id}/tasks/dashboard` | Dashboard stats |
| PATCH | `/api/projects/{id}/tasks/{tid}/status` | Transition task (review-gated) |
| GET/POST | `/api/projects/{id}/memory` | Memory Graph CRUD (append-only) |
| GET | `/api/projects/{id}/memory/graph` | Memory graph with edges |
| GET/POST | `/api/projects/{id}/reviews` | Review management |
| POST | `/api/projects/{id}/reviews/{rid}/approve` | Approve review |
| POST | `/api/projects/{id}/reviews/{rid}/request-changes` | Request changes |
| GET | `/api/projects/{id}/git/log` | Git commit log |
| GET | `/api/projects/{id}/git/branches` | List branches |
| POST | `/api/projects/{id}/git/commit` | Agent commits work |
| POST | `/api/projects/{id}/git/pr` | Create PR |
| GET | `/api/projects/{id}/git/prs` | List PRs |
| POST | `/api/projects/{id}/git/pr/{pid}/merge` | Merge PR |
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
