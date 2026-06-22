#!/usr/bin/env python3
"""
StudioOS Worker CLI — Agent de codage intégré.

Usage:
  python -m app.cli                         # Mode REPL interactif
  python -m app.cli "Crée une API todo..."   # Mode one-shot
  python -m app.cli --identity 5            # Connexion en tant qu'agent #5
  python -m app.cli --project 1             # Sélection du projet #1
"""

import argparse
import asyncio
import logging
import sys

from app.cli import display
from app.cli.session import Session
from app.cli.repl import run_repl


def main():
    parser = argparse.ArgumentParser(
        description="StudioOS Worker CLI — Agent de codage intégré",
    )
    parser.add_argument(
        "text", nargs="*",
        help="Mission en une commande (mode one-shot)",
    )
    parser.add_argument(
        "--identity", "-i", type=int, default=None,
        help="ID de l'agent dans StudioOS",
    )
    parser.add_argument(
        "--project", "-p", type=int, default=None,
        help="ID du projet StudioOS",
    )

    args = parser.parse_args()

    session = Session(
        agent_id=args.identity,
        project_id=args.project,
    )

    if args.identity:
        asyncio.run(session.load_identity(args.identity))

    text = " ".join(args.text) if args.text else None

    if text:
        if text.startswith("/"):
            asyncio.run(_handle_one_shot_command(session, text))
        else:
            asyncio.run(_handle_one_shot(session, text))
    else:
        try:
            asyncio.run(run_repl(session))
        except KeyboardInterrupt:
            display.print_info("\nAu revoir !")
        except Exception as e:
            logger = logging.getLogger("studioos.cli")
            logger.exception("Fatal error")
            display.print_error(f"Erreur fatale: {e}")
            sys.exit(1)


async def _handle_one_shot(session: Session, text: str):
    display.print_info(f"Mission: {text[:80]}...")
    result = await session.chat_stream(text)
    display.print_markdown(result)


async def _handle_one_shot_command(session: Session, text: str):
    parts = text.split()
    cmd = parts[0].lower()
    args = parts[1:]
    from app.cli.commands import COMMANDS
    if cmd in COMMANDS:
        await COMMANDS[cmd](args, session)
    else:
        display.print_error(f"Commande inconnue: {cmd}")


if __name__ == "__main__":
    main()
