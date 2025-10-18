"""
Module for the "gvit clone" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.options.clone import target_dir_option, backend_option, verbose_option
from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.utils.utils import get_backend, get_verbose


def clone(
    repo_url: str,
    target_dir: str = target_dir_option,
    backend: str = backend_option,
    verbose: bool = verbose_option
) -> None:
    """Clone a repo and create a virtual environment."""
    target_dir = target_dir or Path(repo_url).stem
    if backend and backend not in SUPPORTED_BACKENDS:
        raise typer.BadParameter(f"Unsupported backend '{backend}'. Supported backends: ({'/'.join(SUPPORTED_BACKENDS)})")
    verbose = verbose or get_verbose()
    backend = backend or get_backend()
    _git_clone(repo_url, target_dir, verbose)
    _create_virtual_env(target_dir, backend, verbose)


def _git_clone(repo_url: str, target_dir: str, verbose: bool) -> None:
    """Function to clone the repository."""
    typer.echo(f"- Cloning repository: {repo_url}...")
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.secho(f"Repository was cloned -> {target_dir}", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError as e:
        typer.secho(f"\nGit clone failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _create_virtual_env(virtual_env_name: str, backend: str, verbose: bool) -> None:
    """Function to create the virtual environment for the repository."""
    typer.echo(f"\n- Creating virtual environment ({backend}): {virtual_env_name}...")
    if backend == "conda":
        # env_name = path.name
        try:
            result = subprocess.run(
                # ["conda", "create", "--prefix", str(path), "--yes", "python"],
                ["conda", "create", "--name", virtual_env_name, "python=3.10", "--yes"],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Conda environment creation failed:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.secho(f"Virtual environment was created -> {virtual_env_name}", fg=typer.colors.GREEN)
