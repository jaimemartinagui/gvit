"""
gvit CLI.
"""

import typer
import toml
from gvit.utils.globals import CONFIG_DIR, CONFIG_FILE

app = typer.Typer(help="gvit - Git-aware Virtual Environment manager")

@app.command()
def clone(url: str):
    """Clone a repo and create a virtual environment."""
    typer.echo(f"Cloning {url} and creating virtual environment...")

@app.command()
def pull():
    """Pull changes and update dependencies."""
    typer.echo("Updating repository and syncing environment...")


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    return toml.load(CONFIG_FILE) if CONFIG_FILE.exists() else {}


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


@app.command()
def config(
    backend: str = typer.Option(
        None,
        "--backend",
        "-b",
        help="Default virtual environment backend (virtualenv/conda/pyenv)",
    ),
    auto_create_env: bool = typer.Option(
        None,
        "--auto-create-env/--no-auto-create-env",
        help="Automatically create environment on git clone",
    ),
    alias_commands: bool = typer.Option(
        None,
        "--alias-commands/--no-alias-commands",
        help="Enable git command aliases",
    ),
):
    """Configure gvit and generate ~/.config/gvit/config.toml configuration file."""
    ensure_config_dir()
    config_data = load_config()

    # -----------------------
    # Interactivo si no se pasa por CLI
    # -----------------------
    if backend is None:
        backend_choice = typer.prompt(
            "Select default virtual environment backend [virtualenv/conda/pyenv]",
            default=config_data.get("general", {}).get("default_venv_backend", "virtualenv"),
        )
        backend = backend_choice.strip()

    if auto_create_env is None:
        auto_create_env = typer.confirm(
            "Enable automatic environment creation on git clone?",
            default=config_data.get("gitvenv", {}).get("auto_create_env", True),
        )

    if alias_commands is None:
        alias_commands = typer.confirm(
            "Enable git command aliases?",
            default=config_data.get("gitvenv", {}).get("alias_commands", True),
        )

    # -----------------------
    # Construir estructura TOML
    # -----------------------
    config_data["general"] = {"default_venv_backend": backend}
    config_data["gitvenv"] = {
        "auto_create_env": auto_create_env,
        "alias_commands": alias_commands,
    }

    save_config(config_data)
    typer.echo(f"Configuration saved to {CONFIG_FILE}")




# # ~/.config/gitvenv/config.toml
# [defaults]
# backend = "conda"          # o "venv", "poetry", "hatch"...
# auto_install = true
# auto_activate = true
# envs_dir = "~/.virtualenvs"

# [overrides]
# "repos/ml-project" = { backend = "venv" }
# "repos/legacy-app" = { backend = "conda" }



# Función de ejemplo para leer configuración en otros comandos
def get_backend() -> str:
    config = load_config()
    return config.get("general", {}).get("default_venv_backend", "virtualenv")


def get_auto_create_env() -> bool:
    config = load_config()
    return config.get("gitvenv", {}).get("auto_create_env", True)


def get_alias_commands() -> bool:
    config = load_config()
    return config.get("gitvenv", {}).get("alias_commands", True)


if __name__ == "__main__":
    app()
