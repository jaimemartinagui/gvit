"""
Module for the "gvit setup" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.utils.utils import (
    load_local_config,
    load_repo_config,
    get_backend,
    get_python,
    get_verbose,
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.env_registry import EnvRegistry
from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.commands._common import create_venv, install_dependencies, show_summary_message


def setup(
    directory: str = typer.Argument(".", help="Directory of the existing repository (defaults to current directory)."),
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment. If not provided, uses directory name."),
    backend: str = typer.Option(None, "--backend", "-b", help=f"Virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})."),
    python: str = typer.Option(None, "--python", "-p", help="Python version for the virtual environment."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Path to base dependencies file."),
    extra_deps: str = typer.Option(None, "--extra-deps", help="Extra dependency groups (e.g. 'dev,test')."),
    no_deps: bool = typer.Option(False, "--no-deps", is_flag=True, help="Skip dependency installation."),
    force: bool = typer.Option(False, "--force", "-f", is_flag=True, help="Overwrite existing environment without confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Set up a virtual environment for an existing repository.

    Creates a virtual environment, installs dependencies, and tracks the environment
    in the registry for an already cloned repository.

    This is useful when you've cloned a repository manually or want to recreate
    the environment for an existing project.
    """
    # 1. Resolve directory
    target_dir = Path(directory).resolve()
    if not target_dir.exists():
        typer.secho(f'Directory "{directory}" does not exist.', fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 2. Check if it is a git repository
    if not (target_dir / ".git").exists():
        typer.secho(f"Directory '{directory}' is not a git repository.", fg=typer.colors.RED)
        typer.echo("Run `gvit init` instead.")
        raise typer.Exit(code=1)

    # 3. Load config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 4. Get remote URL if it exists
    repo_url = _get_remote_url(str(target_dir))
    if repo_url:
        typer.echo(f'- Repository URL: {repo_url}')

    # 5. Load repo config
    repo_config = load_repo_config(str(target_dir))

    # 6. Create virtual environment
    venv_name = venv_name or target_dir.name
    backend = backend or get_backend(local_config)
    python = python or repo_config.get("gvit", {}).get("python") or get_python(local_config)
    validate_backend(backend)
    validate_python(python)
    venv_name = create_venv(venv_name, str(target_dir), backend, python, force, verbose)

    # 7. Install dependencies
    if no_deps:
        resolved_base_deps = None
        resolved_extra_deps = {}
        typer.echo("\n- Skipping dependency installation...✅")
    else:
        resolved_base_deps, resolved_extra_deps = install_dependencies(
            venv_name, backend, str(target_dir), base_deps, extra_deps, repo_config, local_config, verbose
        )

    # 8. Save environment info to registry
    env_registry = EnvRegistry()
    env_registry.save_environment_info(
        venv_name=venv_name,
        repo_path=str(target_dir),
        repo_url=repo_url or "",
        backend=backend,
        python=python,
        base_deps=resolved_base_deps,
        extra_deps=resolved_extra_deps
    )

    # 9. Summary message
    show_summary_message(venv_name, backend, str(target_dir))


def _get_remote_url(repo_dir: str) -> str:
    """Get the remote URL of the repository if it exists."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""
