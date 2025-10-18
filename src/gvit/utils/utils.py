"""
Module with utility functions.
"""

from typing import Any
import importlib.metadata
import pathlib

import toml
import typer

from gvit.utils.globals import CONFIG_DIR, CONFIG_FILE


def get_version() -> str:
    """
    Get version from installed package metadata.
    If not installed (editable mode), read from pyproject.toml.
    """
    try:
        return importlib.metadata.version("gvit")
    except importlib.metadata.PackageNotFoundError:
        pyproject_path = pathlib.Path(__file__).parent.parent.parent / "pyproject.toml"
        if not pyproject_path.exists():
            raise RuntimeError("Could not determine gvit version.")
        version = toml.load(pyproject_path).get("project", {}).get("version")
        if not version:
            raise RuntimeError("Could not determine gvit version.")
        return version


def ensure_config_dir() -> None:
    """Method to create the configuration file if necessary."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Method to load the configuration file."""
    return toml.load(CONFIG_FILE) if CONFIG_FILE.exists() else {}


def save_config(config: dict[str, Any]) -> None:
    """Method to save the configuration file."""
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)
    typer.echo(f"Configuration saved to {CONFIG_FILE}")


def get_backend() -> str:
    config = load_config()
    return config.get("general", {}).get("default_venv_backend", "virtualenv")


def get_verbose() -> str:
    config = load_config()
    return config.get("general", {}).get("verbose", False)







def get_auto_create_env() -> bool:
    config = load_config()
    return config.get("gitvenv", {}).get("auto_create_env", True)


def get_alias_commands() -> bool:
    config = load_config()
    return config.get("gitvenv", {}).get("alias_commands", True)
