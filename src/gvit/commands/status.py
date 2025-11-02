"""
Module for the "gvit status" command.
"""

from pathlib import Path

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, get_verbose
from gvit.utils.validators import validate_directory, validate_git_repo
from gvit.backends.common import get_freeze, get_freeze_diff, show_freeze_diff
from gvit.git import Git


def status(
    ctx: typer.Context,
    target_dir: str = typer.Option(".", "--target-dir", "-t", help="Directory of the repository (defaults to current directory)."),
    environment: bool = typer.Option(False, "--environment", "-e", is_flag=True, help="Show the status of the environment."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Show repository status and, optionally, the environment status.

    Displays:

    - Git repository status (git status output).

    - Environment status if -e is provided (packages added/removed/modified since last tracking).
    """
    # 1. Resolve and validate directory
    target_dir_ = Path(target_dir).resolve()
    validate_directory(target_dir_)

    # 2. Check if it is a git repository
    validate_git_repo(target_dir_)

    # 3. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 4. Show repository status
    typer.secho("═══════════════════════════════════════════════════════════", fg=typer.colors.CYAN, bold=True)
    typer.secho("  📂 Repository Status", fg=typer.colors.CYAN, bold=True)
    typer.secho("═══════════════════════════════════════════════════════════\n", fg=typer.colors.CYAN, bold=True)

    git = Git()
    git.status(target_dir_, ctx.args)

    if not environment:
        return None

    # 5. Show environment status
    typer.secho("\n═══════════════════════════════════════════════════════════", fg=typer.colors.MAGENTA, bold=True)
    typer.secho("  🐍 Environment Status", fg=typer.colors.MAGENTA, bold=True)
    typer.secho("═══════════════════════════════════════════════════════════", fg=typer.colors.MAGENTA, bold=True)

    env_registry = EnvRegistry()
    envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == target_dir_]

    if not envs:
        typer.secho("\n  ⚠️  No tracked environment found for this repository.", fg=typer.colors.YELLOW)
        typer.echo("  Run `gvit setup` to track this repository.\n")
        return None

    env = envs[0]
    venv_name = Path(env["environment"]["path"]).name
    backend = env["environment"]["backend"]
    repo_path = Path(env["repository"]["path"])
    stored_freeze = env.get("deps", {}).get("installed", {}).get("_freeze", "")

    typer.echo(f'\n  Environment: {env["environment"]["name"]}')
    typer.echo(f"  Backend: {backend}")
    typer.echo(f"  Path: {env['environment']['path']}")

    if not stored_freeze:
        typer.echo("\n  ⚠️  No freeze snapshot found in registry.")
        typer.echo("  Dependencies were installed without tracking.\n")
        return None

    current_freeze = get_freeze(venv_name, repo_path, env["repository"]["url"], backend)

    if not current_freeze:
        typer.secho("\n  ❗ Unable to get current package list from environment.", fg=typer.colors.RED)
        typer.echo("  The environment may not exist or be corrupted.\n")
        return None

    added, removed, changed = get_freeze_diff(stored_freeze, current_freeze)

    typer.echo()
    show_freeze_diff(added, removed, changed)
