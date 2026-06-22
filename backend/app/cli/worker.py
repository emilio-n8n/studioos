from __future__ import annotations

import logging
from typing import Any

import httpx

from app.cli import display
from app.cli import file_ops
from app.cli.session import Session
from app.cli.llm import LLMClient

logger = logging.getLogger("studioos.cli.worker")

API_BASE = "http://localhost:8000"


async def _parse_files_from_llm(text: str) -> list[dict]:
    import re
    pattern = r'===FILE:([^\n]+)===\n(.*?)(?=\n===FILE:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    return [
        {"path": p.strip(), "content": c.strip()}
        for p, c in matches
    ]


class Worker:
    def __init__(self, session: Session):
        self.session = session
        self.llm = LLMClient()

    async def execute_task(
        self,
        task_id: int,
        task_title: str,
        task_description: str,
        project_id: int,
    ):
        display.print_info(f"Début de la mission #{task_id}: {task_title}")

        step_prompt = (
            f"Tu dois réaliser la mission suivante:\n\n"
            f"Titre: {task_title}\n"
            f"Description: {task_description}\n\n"
            f"Analyse cette mission et décompose-la en 3-5 étapes. "
            f"Retourne uniquement une liste numérotée."
        )
        plan = await self.llm.chat([
            {"role": "system", "content": self.session.get_system_prompt()},
            {"role": "user", "content": step_prompt},
        ])
        display.print_info("Plan d'exécution:")
        display.print_markdown(plan)

        exec_prompt = (
            f"Mission: {task_title}\n"
            f"Description: {task_description}\n\n"
            f"Produis les fichiers nécessaires pour accomplir cette mission.\n\n"
            f"Format: ===FILE:chemin/relatif===contenu du fichier\n\n"
            f"Règles:\n"
            f"- Crée les fichiers dans le répertoire courant\n"
            f"- Chaque fichier doit être complet et fonctionnel\n"
            f"- Utilise le format ===FILE:path===\n"
            f"- Ajoute des commentaires pertinents\n"
            f"- Structure propre et professionnelle"
        )

        display.print_info("Génération des fichiers...")
        response = await self.llm.chat([
            {"role": "system", "content": self.session.get_system_prompt()},
            {"role": "user", "content": exec_prompt},
        ])

        files = await _parse_files_from_llm(response)
        if not files:
            display.print_warning(
                "Aucun fichier parsé. Réponse brute:"
            )
            display.print_markdown(response)
            return

        display.print_success(f"{len(files)} fichiers générés:")
        for f in files:
            file_ops.write_file(f["path"], f["content"])
            display.print_success(f"  {f['path']} ({len(f['content'])} octets)")

        should_commit = input(
            "\nCommit et crée une PR ? (O/n): "
        ).strip().lower() or "o"

        if should_commit == "o":
            result = file_ops.git_commit(
                f"feat: {task_title[:60]}"
            )
            display.print_success(f"Commit: {result}")

            try:
                async with httpx.AsyncClient() as client:
                    # Find agent name for branch
                    resp = await client.post(
                        f"{API_BASE}/api/projects/{project_id}/git/commit",
                        json={
                            "agent_id": self.session.agent_id or 1,
                            "files": {
                                f["path"]: f["content"]
                                for f in files
                            },
                            "message": f"Task #{task_id}: {task_title}",
                        },
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        sha = resp.json().get("hexsha", "")
                        display.print_success(f"Commit git: {sha[:8]}")

                        # Create PR
                        pr_resp = await client.post(
                            f"{API_BASE}/api/projects/"
                            f"{project_id}/git/pr",
                            json={
                                "agent_id": self.session.agent_id or 1,
                                "title": f"Task #{task_id}: {task_title}",
                                "description": task_description,
                            },
                            timeout=30,
                        )
                        if pr_resp.status_code == 200:
                            pr_data = pr_resp.json()
                            display.print_success(
                                f"PR #{pr_data.get('pr_id', '?')} créée"
                            )

            except Exception as e:
                logger.warning(f"Git operation failed: {e}")

        display.print_success(f"Mission #{task_id} terminée !")
