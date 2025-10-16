"""
Module for the "gvit clone" command.
"""

import typer


def clone(url: str):
    """Clone a repo and create a virtual environment."""
    typer.echo(f"Cloning {url} and creating virtual environment...")
