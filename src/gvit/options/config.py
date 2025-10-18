"""
Module for the options of the "gvit config" command.
"""

import typer


backend_option = typer.Option(
    None, "--backend", "-b", help="Default virtual environment backend (virtualenv/conda/pyenv)",
)

auto_create_env_option = typer.Option(
    None,
    "--auto-create-env/--no-auto-create-env",
    help="Automatically create environment on git clone",
)

alias_commands_option = typer.Option(
    None,
    "--alias-commands/--no-alias-commands",
    help="Enable git command aliases",
)
