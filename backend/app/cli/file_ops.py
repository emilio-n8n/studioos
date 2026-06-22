import os
import subprocess
from pathlib import Path


def read_file(path: str) -> str:
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> bool:
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return True


def edit_file(path: str, old_text: str, new_text: str) -> bool:
    content = read_file(path)
    if old_text not in content:
        return False
    new_content = content.replace(old_text, new_text)
    write_file(path, new_content)
    return True


def list_directory(path: str = ".") -> list[str]:
    p = Path(path).resolve()
    if not p.exists():
        return []
    entries = []
    gitignore = _load_gitignore(p)
    for child in p.iterdir():
        if _is_ignored(child.name, gitignore):
            continue
        entries.append(str(child.relative_to(p)))
    return entries


def git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--no-color"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def git_diff_stat() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def git_commit(message: str) -> str:
    try:
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, timeout=10,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except Exception as e:
        return str(e)


def git_log(max_count: int = 5) -> list[dict]:
    try:
        result = subprocess.run(
            [
                "git", "log", f"--max-count={max_count}",
                "--format=%h|%an|%s|%ar",
            ],
            capture_output=True, text=True, timeout=5,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "message": parts[2],
                    "date": parts[3],
                })
        return commits
    except Exception:
        return []


def git_branches() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "branch"],
            capture_output=True, text=True, timeout=5,
        )
        return [
            b.strip() for b in result.stdout.strip().split("\n") if b.strip()
        ]
    except Exception:
        return []


def _load_gitignore(path: Path) -> set[str]:
    gitignore_path = path / ".gitignore"
    if gitignore_path.exists():
        return {
            line.strip()
            for line in gitignore_path.read_text().split("\n")
            if line.strip() and not line.startswith("#")
        }
    return set()


def _is_ignored(name: str, gitignore: set[str]) -> bool:
    for pattern in gitignore:
        if name == pattern or pattern.endswith("/") and name == pattern.rstrip("/"):
            return True
    return False
