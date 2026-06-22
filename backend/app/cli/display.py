import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console()

STREAM_DELAY = 0.008


def print_markdown(text: str):
    console.print(Markdown(text))


def print_streaming(text: str):
    for char in text:
        console.print(char, end="", style="white")
    console.print()


async def stream_markdown(
    text: str, on_token=None
):
    words = text.split(" ")
    for i, word in enumerate(words):
        token = word + (" " if i < len(words) - 1 else "")
        if on_token:
            await on_token(token)
        else:
            console.print(token, end="", style="white")
        await asyncio.sleep(STREAM_DELAY)
    if not on_token:
        console.print()


def print_success(msg: str):
    console.print(f"  [bold green]✓[/] {msg}")


def print_error(msg: str):
    console.print(f"  [bold red]✗[/] {msg}")


def print_info(msg: str):
    console.print(f"  [blue]ℹ[/] {msg}")


def print_warning(msg: str):
    console.print(f"  [yellow]⚠[/] {msg}")


def print_table(headers: list[str], rows: list[list]):
    table = Table(
        *headers,
        box=box.SIMPLE,
        header_style="bold cyan",
    )
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def print_tree_data(
    nodes: list[dict], edges: list[dict],
    highlight_id: str | None = None,
):
    children_map: dict[str, list[dict]] = {}
    node_map: dict[str, dict] = {}
    for n in nodes:
        node_map[n["id"]] = n
        if n["id"] not in children_map:
            children_map[n["id"]] = []
    for e in edges:
        if e["source"] not in children_map:
            children_map[e["source"]] = []
        children_map[e["source"]].append(node_map[e["target"]])

    roots = [
        n
        for n in nodes
        if not any(e["target"] == n["id"] for e in edges)
    ]

    tree = Tree("[bold]Organisation[/]")

    def add_nodes(parent: Tree, items: list[dict]):
        for item in items:
            label = item["data"].get("label", item["id"])
            is_highlight = item["id"] == highlight_id
            if is_highlight:
                label = f"[bold green]{label} ← vous[/]"
            subtype = item.get("type", "")
            if subtype == "department":
                child = parent.add(f"[cyan]{label}[/]")
            elif subtype == "role":
                child = parent.add(f"[yellow]{label}[/]")
            else:
                child = parent.add(f"[white]{label}[/]")
            children = children_map.get(item["id"], [])
            if children:
                add_nodes(child, children)

    add_nodes(tree, roots)
    console.print(tree)


@asynccontextmanager
async def Spinner(message: str = "..."):
    import sys
    console.print(f"  [dim]{message}[/]", end="")
    sys.stdout.flush()
    try:
        yield
    finally:
        console.print()


def print_code(
    code: str, language: str = "python",
    title: str | None = None,
):
    syntax = Syntax(
        code, language,
        theme="monokai",
        line_numbers=True,
    )
    if title:
        console.print(Panel(syntax, title=title, border_style="blue"))
    else:
        console.print(Panel(syntax, border_style="blue"))


def fmt_badge(text: str, color: str = "blue") -> str:
    return f"[bold {color} on {color}_dim] {text} [/]"


def welcome_banner(agent_name: str | None, role: str | None, dept: str | None):
    title = Text()
    title.append("╭" + "─" * 56 + "╮\n", style="blue")
    title.append("│", style="blue")
    title.append(" StudioOS Worker CLI ", style="bold cyan")
    title.append("│\n", style="blue")
    if agent_name:
        title.append("│ ", style="blue")
        title.append(f"  Agent: {agent_name}", style="white")
        title.append("│\n", style="blue")
    if role:
        title.append("│ ", style="blue")
        title.append(f"  Rôle: {role}", style="white")
        title.append("│\n", style="blue")
    if dept:
        title.append("│ ", style="blue")
        title.append(f"  Département: {dept}", style="white")
        title.append("│\n", style="blue")
    title.append("│", style="blue")
    title.append(" Tape /help pour les commandes, /exit pour quitter", style="dim")
    title.append("│\n", style="blue")
    title.append("╰" + "─" * 56 + "╯", style="blue")
    console.print(title)
