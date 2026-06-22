from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from app.cli import display
from app.cli.commands import COMMANDS
from app.cli.session import Session

logger = logging.getLogger("studioos.cli.repl")

HISTORY_FILE = str(Path.home() / ".studioos_history")

COMMANDS_LIST = sorted(COMMANDS.keys())


async def run_repl(session: Session):
    display.welcome_banner(
        session.agent_name,
        session.role_title,
        session.department_name,
    )

    completer = WordCompleter(COMMANDS_LIST, ignore_case=True)
    bindings = KeyBindings()

    prompt_session = PromptSession(
        history=FileHistory(HISTORY_FILE),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        key_bindings=bindings,
    )

    agent_label = session.agent_name or "Agent"

    while True:
        try:
            text = await prompt_session.prompt_async(
                f"👤 {agent_label} > ",
                style="class:prompt",
            )
        except (KeyboardInterrupt, EOFError):
            display.print_info("Au revoir !")
            break

        text = text.strip()
        if not text:
            continue

        if text.startswith("/"):
            parts = text.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in COMMANDS:
                try:
                    await COMMANDS[cmd](args, session)
                except SystemExit:
                    break
                except Exception as e:
                    logger.exception(f"Command {cmd} failed")
                    display.print_error(f"Erreur: {e}")
            else:
                display.print_error(
                    f"Commande inconnue: {cmd}. Tape /help"
                )
        else:
            async with display.Spinner("🤖 Réflexion..."):
                await session.chat_stream(
                    text,
                    on_token=lambda t: None,
                )
            # Display the last assistant message
            if session.history:
                last = session.history[-1]
                if last["role"] == "assistant":
                    display.print_markdown(last["content"])
