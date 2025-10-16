"""
Module for the "gvit pull" command.
"""

import typer


def pull():
    """Pull changes and update dependencies."""
    typer.echo("Updating repository and syncing environment...")
