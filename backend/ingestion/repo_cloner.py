"""
repo_cloner.py — Clone a GitHub repository to a local temp directory.
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

import git
from rich.console import Console

from backend.config import get_settings

console = Console()
settings = get_settings()


def _repo_slug(url: str) -> str:
    """Convert a GitHub URL to a filesystem-safe slug."""
    url = url.rstrip("/").removesuffix(".git")
    match = re.search(r"github\.com[:/](.+)", url)
    if match:
        return match.group(1).replace("/", "__")
    return re.sub(r"[^\w\-]", "_", url)[-60:]


def clone_repo(url: str, force: bool = False) -> Path:
    """
    Clone *url* into <repos_dir>/<slug>.
    If the repo already exists, pull latest unless *force* re-clones.

    Returns the local Path to the cloned repo root.
    """
    slug = _repo_slug(url)
    dest = Path(settings.repos_dir) / slug
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        if force:
            shutil.rmtree(dest)
            console.print(f"[yellow]Removed existing clone — re-cloning[/yellow]")
        else:
            console.print(f"[green]Repo already cloned at {dest} — pulling latest[/green]")
            try:
                repo = git.Repo(dest)
                repo.remotes.origin.pull()
            except Exception as e:
                console.print(f"[yellow]Pull failed ({e}), using existing clone[/yellow]")
            return dest

    console.print(f"[cyan]Cloning {url} → {dest}[/cyan]")
    git.Repo.clone_from(url, dest, depth=1)   # shallow clone — fast
    console.print(f"[green]✓ Cloned successfully[/green]")
    return dest
