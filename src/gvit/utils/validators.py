"""
Module with option validators.
"""

from pathlib import Path

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS, SUPPORTED_PYTHONS


def validate_backend(backend: str) -> None:
    """Function to validate the provided backend."""
    if backend not in SUPPORTED_BACKENDS:
        raise typer.BadParameter(f'Unsupported backend "{backend}". Supported backends: {", ".join(SUPPORTED_BACKENDS)}.')


def validate_python(python: str) -> None:
    """Function to validate the provided Python version."""
    if python not in SUPPORTED_PYTHONS:
        raise typer.BadParameter(f'Unsupported Python version "{python}". Supported versions: {", ".join(SUPPORTED_PYTHONS)}.')


def validate_directory(directory: Path) -> None:
    """Function to validate the provided directory."""
    if not directory.exists():
        typer.secho(f'Directory "{directory}" does not exist.', fg=typer.colors.RED)
        raise typer.Exit(code=1)


def validate_git_repo(directory: Path) -> None:
    """Function to validate the provided directory is a git repository."""
    if not (directory / ".git").exists():
        typer.secho(f'Directory "{directory}" is not a Git repository.', fg=typer.colors.RED)
        typer.echo("Run `gvit init` to initialize the repository.")
        raise typer.Exit(code=1)
