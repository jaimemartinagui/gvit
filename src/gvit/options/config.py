"""
Module for the options of the "gvit config" command.
"""

from typer import Option
from gvit.utils.globals import SUPPORTED_BACKENDS


backend_option = Option(
    None, "--backend", "-b", help=f"Default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)}).",
)

# auto_activate_env_option = Option(
#     None,
#     "--auto-create-env/--no-auto-create-env",
#     help="Automatically activate environment on git clone",
# )

auto_create_env_option = Option(
    None,
    "--auto-create-env/--no-auto-create-env",
    help="Automatically create environment on git clone",
)

alias_commands_option = Option(
    None, "--alias-commands/--no-alias-commands", help="Enable git command aliases",
)
