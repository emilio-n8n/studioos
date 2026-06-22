from __future__ import annotations

import logging
from typing import Any

from app.cli.llm import LLMClient

logger = logging.getLogger("studioos.cli.session")

MAX_HISTORY = 50
DEFAULT_AGENT_ID = 1
DEFAULT_PROJECT_ID = 1

SYSTEM_PROMPT_TEMPLATE = """Tu es un agent de codage dans l'organisation StudioOS.

Identité:
- Nom: {agent_name}
- Rôle: {role_title}
- Département: {department_name}
- Supérieur direct: {superior_name}

Mission actuelle: {current_task}

Ton rôle est d'exécuter les missions que ton supérieur te confie.
Tu codes, tu crées des fichiers, tu commites, tu crées des PRs.

Règles:
- Si une mission est ambiguë, pose des questions à ton supérieur
- Produis des fichiers avec le format ===FILE:chemin===contenu
- Fais un commit après chaque étape significative
- Crée une PR quand la mission est terminée
- Reste professionnel et efficace
- Réponds en français
- Sois précis et concis"""


class Session:
    def __init__(
        self,
        agent_id: int | None = None,
        project_id: int | None = None,
    ):
        self.agent_id = agent_id
        self.agent_name: str | None = None
        self.role_title: str | None = None
        self.role_level: int = 1
        self.department_name: str | None = None
        self.department_id: int | None = None
        self.superior_name: str | None = None
        self.superior_id: int | None = None
        self.project_id = project_id
        self.project_name: str | None = None
        self.current_task_id: int | None = None
        self.current_task_title: str | None = None
        self.history: list[dict[str, str]] = []
        self.llm = LLMClient()
        self._loaded = False

    async def load_identity(self, agent_id: int) -> bool:
        """Load agent identity from StudioOS database."""
        try:
            # Import all models to ensure relationships resolve
            import app.models.project  # noqa: F401
            import app.models.organization  # noqa: F401
            import app.models.department  # noqa: F401
            import app.models.role  # noqa: F401
            import app.models.agent  # noqa: F401
            import app.models.task  # noqa: F401

            from app.database import init_db, SessionLocal
            init_db()

            from app.models.agent import Agent
            from app.models.role import Role
            from app.models.department import Department

            db = SessionLocal()
            try:
                agent = db.query(Agent).filter(
                    Agent.id == agent_id
                ).first()
                if not agent:
                    return False

                self.agent_id = agent.id
                self.agent_name = agent.name

                role = db.query(Role).filter(
                    Role.id == agent.role_id
                ).first()
                if role:
                    self.role_title = role.title
                    self.role_level = role.level or 1
                    dept = db.query(Department).filter(
                        Department.id == role.department_id
                    ).first()
                    if dept:
                        self.department_name = dept.name
                        self.department_id = dept.id

                    # Find superior (agent with Lead/Director role in same dept)
                    superior = (
                        db.query(Agent)
                        .join(Role, Agent.role_id == Role.id)
                        .filter(
                            Role.department_id == role.department_id,
                            Role.is_governance == True,
                            Agent.id != agent.id,
                        )
                        .first()
                    )
                    if superior:
                        self.superior_name = superior.name
                        self.superior_id = superior.id
                    else:
                        self.superior_name = "Système"
                else:
                    self.role_title = "Worker"
                    self.department_name = "General"

                self._loaded = True
                return True

            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load identity: {e}")
            self.agent_name = "Worker"
            self.role_title = "Worker"
            self.department_name = "General"
            self.superior_name = "Système"
            self._loaded = True
            return True

    def get_system_prompt(self) -> str:
        current_task = (
            f"#{self.current_task_id}: {self.current_task_title}"
            if self.current_task_id
            else "Aucune"
        )
        return SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=self.agent_name or "Agent",
            role_title=self.role_title or "Worker",
            department_name=self.department_name or "General",
            superior_name=self.superior_name or "Système",
            current_task=current_task,
        )

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]

    async def chat_stream(
        self,
        message: str,
        on_token=None,
    ):
        self.add_message("user", message)
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
        ]
        # Use last 20 messages for context window
        for msg in self.history[-20:]:
            messages.append(msg)

        response = await self.llm.chat_stream(messages, on_token)
        self.add_message("assistant", response)
        return response

    def get_token_summary(self) -> str:
        tokens = self.llm.get_token_summary()
        return (
            f"Tokens: {tokens['input']} entrée / {tokens['output']} sortie "
            f"| Coût estimé: ${tokens['estimated_cost']:.4f}"
        )

    def clear_history(self):
        self.history = []
