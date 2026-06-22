# StudioOS CLI — Agent de codage intégré

## Vision

Le CLI est l'**agent de codage intégré** à StudioOS. Il se situe au même niveau qu'un agent ACP externe dans la hiérarchie.

```
Agents de gouvernance (existants, déjà développés)
├── CEO (stratégie, vision)
├── Directeurs (direction par département)
├── Leads (supervision d'équipe)
├── Strategic Planner (planification)
├── Recruiter (recrutement par compétences)
├── Reviewers (validation qualité)
└── QA Supervisors (contrôle qualité)
    │
    │  Assignent des tâches → review → approbation
    ▼
Agents de codage (exécution)
├── Agent ACP externe (protocole HTTP distant) ✓ DÉJÀ FAIT
└── Agent CLI intégré (python -m app.cli)       ← À CONSTRUIRE
    │
    ├── Reçoit des missions de son Lead
    ├── Pose des questions si besoin
    ├── Code (crée/modifie des fichiers)
    ├── Commit → PR → review
    └── Reporte au supérieur
```

## Identité

Le CLI s'exécute **en tant qu'agent de codage** dans l'organisation :

- Il a un rôle (Backend Developer, Frontend Developer, etc.)
- Il est rattaché à un département (Engineering, Design, etc.)
- Il a un supérieur direct (un Lead agent)
- Il a des coéquipiers (même département)
- Il peut communiquer avec d'autres départements (ex: `/delegate`)

## Fonctionnement

```
$ python -m app.cli

╭──────────────────────────────────────────────────────╮
│  Agent de Codage #3                                  │
│  Rôle: Backend Developer · Engineering               │
│  Supérieur: Morgan (Tech Lead)                       │
│  Tâches en attente: 2                                │
│  Coéquipiers: Alex, Sam, Jordan                      │
╰──────────────────────────────────────────────────────╯

/tasks
  #42 [À faire] Créer API todos - par Morgan

/tasks start 42
🤖 Mission reçue ! Je commence l'analyse...

→ Tu veux une API REST ou GraphQL ?

Supérieur > REST, SQLite

🤖 OK, je code...
  ✓ app/main.py créé
  ✓ app/models.py créé
  ✓ Tests créés
  ✓ Commit "feat: todo REST API"
  ✓ PR #42 créée pour review

Supérieur > Envoie une mission au département 3D : "Créez un dragon"
🤖 Je transmets au Responsable 3D...
  ✓ Mission transmise à Jordan (3D Lead)
  → Suivi: /status mission-43

/tasks report 42
✓ Notification envoyée à Morgan (Tech Lead)
```

## Architecture

```
backend/app/cli/
├── __init__.py         # Version
├── main.py             # python -m app.cli [--identity "agent-5"]
├── repl.py             # Boucle interactive (prompt_toolkit)
├── worker.py           # Exécution d'une mission
├── commands.py         # Commandes : /tasks, /delegate, /team...
├── display.py          # rich : markdown streamé, spinners
├── session.py          # Contexte : identité, historique, tokens
├── llm.py              # Appels LLM avec streaming
└── file_ops.py         # Lecture/écriture/édition fichiers
```

## Commandes

| Commande | Action |
|----------|--------|
| `texte libre` | Mission ou question (chat direct) |
| `/tasks` | Liste les tâches assignées |
| `/tasks start <id>` | Commence une mission |
| `/tasks report <id>` | Marque comme terminée + notifie le Lead |
| `/delegate "msg" --to dept:nom` | Envoie une mission à un autre département |
| `/team` | Liste les coéquipiers du département |
| `/org` | Arbre hiérarchique complet |
| `/whoami` | Mon identité, mon rôle, mon supérieur |
| `/status` | Mission en cours, tokens |
| `/plan` | Décompose la mission en étapes |
| `/commit "msg"` | Git add + commit |
| `/diff` | Modifications en cours |
| `/read <path>` | Affiche un fichier |
| `/write <path>` | Écrit un fichier |
| `/edit <path>` | Modifie un fichier via LLM |
| `/run <cmd>` | Exécute une commande shell |
| `/cost` | Tokens + coût estimé |
| `/project list` | Liste les projets StudioOS |
| `/project select <id>` | Sélectionne un projet actif |
| `/help` | Aide |
| `/clear` | Vide l'historique |
| `/exit` | Quitte |

## Dépendances

- `rich` — terminal formatting (déjà installé)
- `prompt_toolkit` — REPL loop (déjà installé)
- `GitPython` — git operations (déjà installé)
- `openai` — LLM calls (déjà installé)
- `httpx` — HTTP client (déjà installé)

## Fichiers à créer (9)

| Fichier | Lignes | Rôle |
|---------|--------|------|
| `cli/__init__.py` | 5 | Version |
| `cli/main.py` | 60 | Entry point, parse --identity |
| `cli/repl.py` | 130 | REPL loop avec prompt_toolkit |
| `cli/worker.py` | 120 | Exécution de mission |
| `cli/commands.py` | 400 | Toutes les commandes |
| `cli/display.py` | 150 | Rich formatting, streaming |
| `cli/session.py` | 120 | Contexte, identité, historique, tokens |
| `cli/llm.py` | 80 | Appels LLM avec streaming |
| `cli/file_ops.py` | 60 | File operations |

Total : ~1125 lignes
