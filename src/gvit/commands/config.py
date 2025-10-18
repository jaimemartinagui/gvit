"""
Module for the "gvit config" command.
"""

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.options.config import backend_option, auto_create_env_option, alias_commands_option
from gvit.utils.utils import ensure_config_dir, load_config, save_config


def config(
    backend: str = backend_option,
    # auto_activate_env: bool = auto_create_env_option,
    # auto_create_env: bool = auto_create_env_option,
    # alias_commands: bool = alias_commands_option,
) -> None:
    """Configure gvit and generate ~/.config/gvit/config.toml configuration file."""
    ensure_config_dir()
    config_data = load_config()

    if backend and backend not in SUPPORTED_BACKENDS:
        raise typer.BadParameter(f"Unsupported backend '{backend}'. Supported backends: ({'/'.join(SUPPORTED_BACKENDS)})")

    if backend is None:
        backend_choice = typer.prompt(
            f"Select default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})",
            default=config_data.get("defaults", {}).get("backend", "venv"),
        ).strip()
        print(backend_choice)

    # if auto_create_env is None:
    #     auto_create_env = typer.confirm(
    #         "Enable automatic environment creation on git clone?",
    #         default=config_data.get("gitvenv", {}).get("auto_create_env", True),
    #     )

    # if alias_commands is None:
    #     alias_commands = typer.confirm(
    #         "Enable git command aliases?",
    #         default=config_data.get("gitvenv", {}).get("alias_commands", True),
    #     )

    # config_data["general"] = {"default_venv_backend": backend}
    # config_data["gitvenv"] = {
    #     "auto_create_env": auto_create_env,
    #     "alias_commands": alias_commands,
    # }

    # save_config(config_data)






# # ~/.config/gitvenv/config.toml
# [defaults]
# backend = "conda"          # o "venv", "poetry", "hatch"...
# auto_install = true
# auto_activate = true
# envs_dir = "~/.virtualenvs"

# [overrides]
# "repos/ml-project" = { backend = "venv" }
# "repos/legacy-app" = { backend = "conda" }
