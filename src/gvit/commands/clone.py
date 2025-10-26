"""
Module for the "gvit clone" command.
"""

import subprocess

import typer

from gvit.utils.utils import (
    load_local_config,
    load_repo_config,
    get_backend,
    get_python,
    get_verbose,
    extract_repo_name_from_url,
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.env_registry import EnvRegistry
from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.commands._common import create_venv, install_dependencies, show_summary_message


def clone(
    ctx: typer.Context,
    repo_url: str = typer.Argument(help="Repository URL."),
    target_dir: str = typer.Option(None, "--target-dir", "-t", help="Directory to clone into."),
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment to create. If not provided it will take it from the repository name."),
    backend: str = typer.Option(None, "--backend", "-b", help=f"Virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})."),
    python: str = typer.Option(None, "--python", "-p", help="Python version for the virtual environment."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Path to base dependencies file (overrides repo/local config)."),
    extra_deps: str = typer.Option(None, "--extra-deps", help="Extra dependency groups (e.g. 'dev,test' or 'dev:path.txt,test:path2.txt')."),
    no_deps: bool = typer.Option(False, "--no-deps", is_flag=True, help="Skip dependency installation."),
    force: bool = typer.Option(False, "--force", "-f", is_flag=True, help="Overwrite existing environment without confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Clone a Git repository and create a virtual environment.

    Any extra options will be passed directly to the `git clone` command.

    Long options do not conflict between `gvit clone` and `git clone`.

    Short options might conflict; in that case, use the long form for the `git clone` options.
    """
    # 1. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 2. Clone repo
    target_dir = target_dir or extract_repo_name_from_url(repo_url)
    _clone_repo(repo_url, target_dir, verbose, ctx.args)

    # 3. Load repo config
    repo_config = load_repo_config(target_dir)

    # 4. Create virtual environment
    backend = backend or get_backend(local_config)
    python = python or repo_config.get("gvit", {}).get("python") or get_python(local_config)
    validate_backend(backend)
    validate_python(python)
    registry_name, venv_name, venv_path = create_venv(venv_name, target_dir, backend, python, force, verbose)

    # 5. Install dependencies
    if no_deps:
        resolved_base_deps = None
        resolved_extra_deps = {}
        typer.echo("\n- Skipping dependency installation...✅")
    else:
        resolved_base_deps, resolved_extra_deps = install_dependencies(
            venv_name=venv_name,
            backend=backend,
            repo_path=target_dir,
            base_deps=base_deps,
            extra_deps=extra_deps,
            repo_config=repo_config,
            local_config=local_config,
            verbose=verbose
        )

    # 6. Save environment info to registry
    env_registry = EnvRegistry()
    env_registry.save_venv_info(
        venv_name=registry_name,
        venv_path=venv_path,
        repo_path=target_dir,
        repo_url=repo_url,
        backend=backend,
        python=python,
        base_deps=resolved_base_deps,
        extra_deps=resolved_extra_deps
    )

    # 7. Summary message
    show_summary_message(registry_name)


def _clone_repo(repo_url: str, target_dir: str, verbose: bool, extra_args: list[str] | None = None) -> None:
    """Function to clone the repository."""
    typer.echo(f"- Cloning repository {repo_url}...", nl=False)
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir] + (extra_args or []),
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.echo("✅")
    except subprocess.CalledProcessError as e:
        typer.secho(f"❗ Git clone failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
