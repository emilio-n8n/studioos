from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from app.cli import display
from app.cli import file_ops
from app.cli.session import Session

logger = logging.getLogger("studioos.cli.commands")

API_BASE = "http://localhost:8000"


async def _api_get(path: str) -> Any:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json()


async def _api_post(path: str, data: dict | None = None) -> Any:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}{path}",
            json=data or {},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()


async def _api_patch(path: str, data: dict) -> Any:
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{API_BASE}{path}",
            json=data,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def cmd_help(args: list[str], session: Session):
    display.print_markdown(
        """
## Commandes StudioOS CLI

| Commande | Description |
|----------|-------------|
| `texte libre` | Mission ou question (chat direct avec LLM) |
| `/tasks` | Liste mes tâches |
| `/tasks start <id>` | Commencer une mission |
| `/tasks report <id>` | Terminer + notifier le Lead |
| `/delegate "msg" --to dept:<nom>` | Envoyer une mission à un département |
| `/team` | Mes coéquipiers |
| `/org` | Arbre hiérarchique |
| `/whoami` | Mon identité |
| `/status` | Mission en cours, git, tokens |
| `/plan` | Décomposer la mission en étapes |
| `/commit "message"` | Git add + commit |
| `/diff` | Modifications en cours |
| `/read <path>` | Afficher un fichier |
| `/write <path>` | Écrire un fichier |
| `/edit <path>` | Modifier un fichier via LLM |
| `/run <cmd>` | Exécuter une commande shell |
| `/cost` | Tokens et coût |
| `/project list` | Projets StudioOS |
| `/project select <id>` | Sélectionner un projet |
| `/clear` | Vider l'historique |
| `/exit` | Quitter |
"""
    )


async def cmd_tasks(args: list[str], session: Session):
    if not session.project_id:
        display.print_warning(
            "Aucun projet sélectionné. Utilise /project select <id>"
        )
        return

    pid = session.project_id

    if args and args[0] == "start" and len(args) > 1:
        tid = int(args[1])
        try:
            await _api_patch(
                f"/api/projects/{pid}/tasks/{tid}/status",
                {"status": "IN_PROGRESS"},
            )
            session.current_task_id = tid
            # Get task title
            tasks = await _api_get(f"/api/projects/{pid}/tasks")
            for t in tasks:
                if t["id"] == tid:
                    session.current_task_title = t.get("title", "")
                    break
            display.print_success(
                f"Mission #{tid} commencée. "
                f"Utilise /plan pour décomposer."
            )
        except Exception as e:
            display.print_error(f"Impossible de démarrer la tâche: {e}")
        return

    if args and args[0] == "report" and len(args) > 1:
        tid = int(args[1])
        try:
            await _api_patch(
                f"/api/projects/{pid}/tasks/{tid}/status",
                {"status": "COMPLETED"},
            )
            session.current_task_id = None
            session.current_task_title = None
            display.print_success(f"Mission #{tid} terminée et notifiée.")
        except Exception as e:
            display.print_error(f"Impossible de finaliser: {e}")
        return

    try:
        data = await _api_get(f"/api/projects/{pid}/tasks")
        if not data:
            display.print_info("Aucune tâche.")
            return
        rows = []
        for t in data:
            rows.append([
                t["id"],
                t.get("title", "")[:50],
                t.get("status", ""),
                t.get("assigned_agent_id", "-"),
            ])
        display.print_table(
            ["#", "Titre", "Statut", "Agent"],
            rows,
        )
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_delegate(args: list[str], session: Session):
    if not args:
        display.print_warning(
            "Usage: /delegate \"mission\" --to department:<nom>"
        )
        return

    text = " ".join(args)
    target = None
    target_type = None

    if "--to" in text:
        parts = text.split("--to")
        message = parts[0].strip().strip("\"'")
        target_part = parts[1].strip()

        if target_part.startswith("department:") or target_part.startswith("dept:"):
            target = target_part.split(":", 1)[1].strip()
            target_type = "department"
        elif target_part.startswith("agent:"):
            target = target_part.split(":", 1)[1].strip()
            target_type = "agent"

    if not target:
        display.print_warning(
            "Usage: /delegate \"mission\" --to department:<nom>"
        )
        return

    display.print_info(
        f"Transmission de mission au {target_type} '{target}'..."
    )

    try:
        if target_type == "department":
            org = await _api_get(
                f"/api/projects/{session.project_id}/organization"
            ) if session.project_id else None
            target_agent = None
            if org:
                for dept in org.get("departments", []):
                    if target.lower() in dept["name"].lower():
                        for role in dept.get("roles", []):
                            if "lead" in role.get("title", "").lower():
                                target_agent = role.get("id")
                                break
            display.print_success(
                f"Mission transmise au département {target}."
            )
        else:
            display.print_success(
                f"Mission transmise à l'agent #{target}."
            )
    except Exception as e:
        display.print_error(f"Échec de transmission: {e}")


async def cmd_team(args: list[str], session: Session):
    if not session.project_id:
        display.print_warning("Aucun projet sélectionné.")
        return

    try:
        data = await _api_get(
            f"/api/projects/{session.project_id}/organization"
        )
        rows = []
        for dept in data.get("departments", []):
            if (
                session.department_name
                and session.department_name.lower()
                not in dept["name"].lower()
            ):
                continue
            for role in dept.get("roles", []):
                for agent in role.get("agents", []):
                    rows.append([
                        agent.get("name", ""),
                        role.get("title", ""),
                        dept.get("name", ""),
                        agent.get("status", ""),
                    ])

        if rows:
            display.print_table(
                ["Nom", "Rôle", "Département", "Statut"], rows
            )
        else:
            display.print_info("Aucun coéquipier trouvé.")
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_org(args: list[str], session: Session):
    if not session.project_id:
        display.print_warning("Aucun projet sélectionné.")
        return

    try:
        data = await _api_get(
            f"/api/projects/{session.project_id}/organization/tree"
        )
        highlight = (
            f"agent-{session.agent_id}" if session.agent_id else None
        )
        display.print_tree_data(
            data.get("nodes", []),
            data.get("edges", []),
            highlight_id=highlight,
        )
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_whoami(args: list[str], session: Session):
    display.print_markdown(
        f"""
## Identité

| Champ | Valeur |
|-------|--------|
| **Nom** | {session.agent_name or 'Non connecté'} |
| **Rôle** | {session.role_title or '-'} |
| **Niveau** | {session.role_level} |
| **Département** | {session.department_name or '-'} |
| **Supérieur** | {session.superior_name or '-'} |
| **Projet** | #{session.project_id} {session.project_name or ''} |
| **Tâche en cours** | #{session.current_task_id} {session.current_task_title or ''} |
"""
    )


async def cmd_status(args: list[str], session: Session):
    await cmd_whoami(args, session)

    git_st = file_ops.git_status()
    if git_st:
        display.print_info(f"Git:\n```\n{git_st}\n```")
    else:
        display.print_info("Git: propre")

    diff = file_ops.git_diff_stat()
    if diff:
        display.print_info(f"Modifications: {diff}")

    display.print_info(session.get_token_summary())


async def cmd_plan(args: list[str], session: Session):
    if not session.current_task_id:
        display.print_warning(
            "Aucune mission sélectionnée. Utilise /tasks start <id>"
        )
        return

    display.print_info("Analyse de la mission en cours...")

    prompt = (
        f"Mission #{session.current_task_id}: "
        f"{session.current_task_title}\n\n"
        f"Décompose cette mission en étapes précises et exécutables. "
        f"Retourne une liste numérotée des fichiers à créer/modifier "
        f"et des actions à réaliser."
    )

    response = await session.chat_stream(prompt)
    display.print_markdown(response)


async def cmd_commit(args: list[str], session: Session):
    message = " ".join(args) if args else None

    if not message:
        diff = file_ops.git_diff()
        if diff:
            display.print_info(
                "Génération du message de commit depuis les changements..."
            )
            prompt = (
                f"Génère un message de commit git concis en français "
                f"pour ces changements:\n\n{diff[:2000]}"
            )
            message = await session.llm.chat([
                {"role": "system", "content": "Génère un message git commit court."},
                {"role": "user", "content": prompt},
            ])
            message = message.strip().split("\n")[0][:100]
        else:
            display.print_warning(
                "Aucun changement à committer."
            )
            return

    result = file_ops.git_commit(message)
    if "nothing to commit" in result.lower():
        display.print_warning("Rien à commit.")
    elif "error" in result.lower():
        display.print_error(f"Commit échoué: {result}")
    else:
        display.print_success(f"Commit: {message}")


async def cmd_diff(args: list[str], session: Session):
    diff = file_ops.git_diff()
    if diff:
        display.print_code(diff, language="diff", title="git diff")
    else:
        display.print_info("Aucune modification.")


async def cmd_read(args: list[str], session: Session):
    if not args:
        display.print_warning("Usage: /read <chemin>")
        return

    path = args[0]
    try:
        content = file_ops.read_file(path)
        ext = path.split(".")[-1] if "." in path else "text"
        lang_map = {
            "py": "python", "js": "javascript", "ts": "typescript",
            "html": "html", "css": "css", "json": "json",
            "md": "markdown", "yaml": "yaml", "yml": "yaml",
            "toml": "toml", "sql": "sql", "sh": "bash",
        }
        lang = lang_map.get(ext, "text")
        display.print_code(content, language=lang, title=path)
    except FileNotFoundError:
        display.print_error(f"Fichier introuvable: {path}")
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_write(args: list[str], session: Session):
    if len(args) < 2:
        display.print_warning("Usage: /write <chemin> <contenu>")
        return

    path = args[0]
    content = " ".join(args[1:])
    try:
        file_ops.write_file(path, content)
        display.print_success(f"{path} écrit ({len(content)} octets)")
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_edit(args: list[str], session: Session):
    if not args:
        display.print_warning("Usage: /edit <chemin> [instruction]")
        return

    path = args[0]
    instruction = " ".join(args[1:]) if len(args) > 1 else None

    try:
        content = file_ops.read_file(path)
    except FileNotFoundError:
        display.print_error(f"Fichier introuvable: {path}")
        return

    if not instruction:
        display.print_info(
            f"Fichier chargé ({len(content)} octets). "
            f"Donne une instruction de modification."
        )
        display.print_code(content, title=path)
        return

    display.print_info("Modification via LLM...")

    prompt = (
        f"Voici le fichier {path}:\n\n"
        f"```\n{content}\n```\n\n"
        f"Instruction: {instruction}\n\n"
        f"Retourne le fichier complet modifié au format "
        f"===FILE:{path}===\ncontenu modifié"
    )

    response = await session.llm.chat([
        {"role": "system", "content": (
            "Tu modifies des fichiers. Retourne le fichier complet "
            "au format ===FILE:chemin===\ncontenu"
        )},
        {"role": "user", "content": prompt},
    ])

    if f"===FILE:{path}===" in response:
        new_content = response.split(f"===FILE:{path}===")[1]
        if "===FILE:" in new_content:
            new_content = new_content.split("===FILE:")[0]
        new_content = new_content.strip()
        file_ops.write_file(path, new_content)
        display.print_success(f"{path} modifié.")
    else:
        display.print_warning(
            "Impossible de parser la réponse. Contenu brut:"
        )
        display.print_markdown(response)


async def cmd_run(args: list[str], session: Session):
    if not args:
        display.print_warning("Usage: /run <commande>")
        return

    command = " ".join(args)
    display.print_info(f"Exécution: {command}")

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=120
        )

        if stdout:
            display.print_code(
                stdout.decode(), language="bash",
                title="stdout",
            )
        if stderr:
            display.print_code(
                stderr.decode(), language="bash",
                title="stderr",
            )

        if proc.returncode == 0:
            display.print_success(
                f"Commande terminée (code: {proc.returncode})"
            )
        else:
            display.print_error(
                f"Commande échouée (code: {proc.returncode})"
            )
    except asyncio.TimeoutError:
        display.print_error("Commande interrompue (120s)")
    except FileNotFoundError:
        display.print_error(f"Commande introuvable: {command}")
    except Exception as e:
        display.print_error(f"Erreur: {e}")


async def cmd_cost(args: list[str], session: Session):
    display.print_info(session.get_token_summary())
    display.print_info(
        "Tarifs: entrée $0.15/1M tokens, sortie $0.60/1M tokens"
    )


async def cmd_project(args: list[str], session: Session):
    sub = args[0] if args else "list"

    if sub == "list":
        try:
            data = await _api_get("/api/projects")
            rows = []
            for p in data:
                rows.append([
                    p["id"], p["name"][:40], p.get("status", ""),
                    p.get("complexity", "-"),
                ])
            display.print_table(
                ["#", "Nom", "Statut", "Complexité"], rows
            )
        except Exception as e:
            display.print_error(f"Erreur: {e}")

    elif sub == "select" and len(args) > 1:
        pid = int(args[1])
        try:
            data = await _api_get(f"/api/projects/{pid}")
            session.project_id = data["id"]
            session.project_name = data.get("name", "")
            display.print_success(
                f"Projet #{pid}: {session.project_name}"
            )
        except Exception as e:
            display.print_error(f"Projet introuvable: {e}")

    elif sub == "create" and len(args) > 2:
        name = args[1]
        desc = " ".join(args[2:])
        try:
            data = await _api_post("/api/projects", {
                "name": name,
                "description": desc,
                "openai_api_key": "demo",
            })
            session.project_id = data["id"]
            session.project_name = data.get("name", "")
            display.print_success(
                f"Projet #{data['id']} créé: {data['name']}"
            )
        except Exception as e:
            display.print_error(f"Erreur: {e}")

    else:
        display.print_warning(
            "Usage: /project list | /project select <id> | "
            "/project create <name> <description>"
        )


async def cmd_clear(args: list[str], session: Session):
    session.clear_history()
    display.print_success("Historique vidé.")


async def cmd_exit(args: list[str], session: Session):
    display.print_info("Au revoir !")
    raise SystemExit(0)


COMMANDS: dict[str, callable] = {
    "/help": cmd_help,
    "/tasks": cmd_tasks,
    "/delegate": cmd_delegate,
    "/team": cmd_team,
    "/org": cmd_org,
    "/whoami": cmd_whoami,
    "/status": cmd_status,
    "/plan": cmd_plan,
    "/commit": cmd_commit,
    "/diff": cmd_diff,
    "/read": cmd_read,
    "/write": cmd_write,
    "/edit": cmd_edit,
    "/run": cmd_run,
    "/cost": cmd_cost,
    "/project": cmd_project,
    "/clear": cmd_clear,
    "/exit": cmd_exit,
}
