"""
Module with option validators.
"""

from pathlib import Path

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS, MIN_PYTHON_VERSION


def validate_backend(backend: str) -> None:
    """Function to validate the provided backend."""
    if backend not in SUPPORTED_BACKENDS:
        raise typer.BadParameter(f'Unsupported backend "{backend}". Supported backends: {", ".join(SUPPORTED_BACKENDS)}.')


def validate_python(python: str) -> None:
    """
    Function to validate the provided Python version.
    Validates that the version is >= MIN_PYTHON_VERSION.
    """
    try:
        parts = python.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid version format")

        major = int(parts[0])
        minor = int(parts[1])

        min_parts = MIN_PYTHON_VERSION.split(".")
        min_major = int(min_parts[0])
        min_minor = int(min_parts[1])

        if (major, minor) < (min_major, min_minor):
            raise typer.BadParameter(
                f'Python version "{python}" is not supported. '
                f'Minimum required version: {MIN_PYTHON_VERSION}'
            )
    except (ValueError, IndexError):
        raise typer.BadParameter(
            f'Invalid Python version format "{python}". '
            f'Expected format: "X.Y" or "X.Y.Z" (e.g., "3.10", "3.11.2")'
        )


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
