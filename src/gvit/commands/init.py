"""
Module for the "gvit init" command.
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
from gvit.utils.validators import validate_backend, validate_python, validate_directory
from gvit.env_registry import EnvRegistry
from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.commands._common import create_venv, install_dependencies, show_summary_message


def init(
    ctx: typer.Context,
    directory: str = typer.Argument(".", help="Directory to initialize (defaults to current directory)."),
    remote_url: str = typer.Option(None, "--remote-url", "-r", help="Remote repository URL to link (sets git remote origin)."),
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
    Initialize a Git repository and create a virtual environment.

    Similar to `git init` but also sets up a virtual environment for the project.

    Any extra options will be passed directly to the `git init` command.

    Long options do not conflict between `gvit init` and `git init`.

    Short options might conflict; in that case, use the long form for the `git init` options.
    """
    # 1. Resolve directory
    target_dir = Path(directory).resolve()
    validate_directory(target_dir)

    # 2. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 3. Initialize git repository
    typer.echo(f'- Initializing Git repository in "{target_dir}"...', nl=False)
    _init_repo(str(target_dir), verbose, ctx.args)

    # 4. Add remote if provided
    repo_url = ""
    if remote_url:
        typer.echo(f'\n- Adding remote origin "{remote_url}"...', nl=False)
        _add_remote(str(target_dir), remote_url, verbose)
        repo_url = remote_url

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
        repo_url=repo_url,
        backend=backend,
        python=python,
        base_deps=resolved_base_deps,
        extra_deps=resolved_extra_deps
    )

    # 9. Summary message
    show_summary_message(venv_name, backend, str(target_dir))


def _init_repo(target_dir: str, verbose: bool = False, extra_args: list[str] | None = None) -> None:
    """Function to initialize the Git repository."""
    try:
        result = subprocess.run(
            ["git", "init"] + (extra_args or []),
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.echo("✅")
    except subprocess.CalledProcessError as e:
        typer.secho(f"❗ Git init failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _add_remote(target_dir: str, remote_url: str, verbose: bool = False) -> None:
    """Add remote origin to the Git repository."""
    try:
        result = subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.echo("✅")
    except subprocess.CalledProcessError as e:
        typer.secho(f"❗ Failed to add remote:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
