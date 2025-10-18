"""
Module with option validators.
"""

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS, SUPPORTED_PYTHONS


def validate_backend(backend) -> None:
    if backend not in SUPPORTED_BACKENDS:
        raise typer.BadParameter(f"Unsupported backend '{backend}'. Supported backends: {', '.join(SUPPORTED_BACKENDS)}.")


def validate_python(python: str) -> None:
    if python not in SUPPORTED_PYTHONS:
        raise typer.BadParameter(f"Unsupported Python version '{python}'. Supported versions: {', '.join(SUPPORTED_PYTHONS)}.")
