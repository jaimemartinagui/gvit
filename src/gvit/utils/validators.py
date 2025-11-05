"""
Module with option validators.
"""

from pathlib import Path

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS, MIN_PYTHON_VERSION
from gvit.error_handler import set_error_message, exit_with_error


def validate_backend(backend: str) -> None:
    """Function to validate the provided backend."""
    if backend not in SUPPORTED_BACKENDS:
        error_msg = f'Unsupported backend "{backend}". Supported backends: {", ".join(SUPPORTED_BACKENDS)}.'
        set_error_message(error_msg)
        raise typer.BadParameter(error_msg)


def validate_python(python: str) -> None:
    """
    Function to validate the provided Python version.
    Validates that the version is >= MIN_PYTHON_VERSION.
    """
    try:
        parts = python.split(".")
        if len(parts) < 2:
            error_msg = "Invalid version format"
            set_error_message(error_msg)
            raise typer.BadParameter(error_msg)

        major = int(parts[0])
        minor = int(parts[1])

        min_parts = MIN_PYTHON_VERSION.split(".")
        min_major = int(min_parts[0])
        min_minor = int(min_parts[1])

        if (major, minor) < (min_major, min_minor):
            error_msg = (
                f'Python version "{python}" is not supported. '
                f'Minimum required version: {MIN_PYTHON_VERSION}'
            )
            set_error_message(error_msg)
            raise typer.BadParameter(error_msg)
    except (ValueError, IndexError):
        error_msg = (
            f'Invalid Python version format "{python}". '
            f'Expected format: "X.Y" or "X.Y.Z" (e.g., "3.10", "3.11.2")'
        )
        set_error_message(error_msg)
        raise typer.BadParameter(error_msg)


def validate_directory(directory: Path) -> None:
    """Function to validate the provided directory."""
    if not directory.exists():
        error_msg = f'❗ Directory "{directory}" does not exist.'
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)


def validate_git_repo(directory: Path) -> None:
    """Function to validate the provided directory is a git repository."""
    if not (directory / ".git").exists():
        error_msg = f'Directory "{directory}" is not a Git repository.'
        typer.secho(error_msg, fg=typer.colors.RED)
        typer.echo("Run `gvit init` to initialize the repository.")
        exit_with_error(error_msg)
