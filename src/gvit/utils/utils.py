"""
Module with utility functions.
"""

from typing import Any
import importlib.metadata
from pathlib import Path

import toml
import typer

from gvit.utils.globals import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_BACKEND,
    DEFAULT_PYTHON,
    DEFAULT_INSTALL_DEPS,
    DEFAULT_DEPS_PATH,
    DEFAULT_ACTIVATE,
    REPO_CONFIG_FILE,
    DEFAULT_VERBOSE
)


def get_version() -> str:
    """
    Get version from installed package metadata.
    If not installed (editable mode), read from pyproject.toml.
    """
    try:
        return importlib.metadata.version("gvit")
    except importlib.metadata.PackageNotFoundError:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
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
    """
    Method to load the configuration file.
    ---------
    [defaults]
    backend = "conda"
    python = "3.11"
    install_deps = true
    deps_path = "pyproject.toml"
    activate = true
    ---------
    """
    return toml.load(CONFIG_FILE) if CONFIG_FILE.exists() else {}


def load_repo_config(repo_path: str) -> dict[str, Any]:
    """
    Method to load the configuration file from the repository.
    It looks for a .gvit.toml file in the root of the repo. If it does not exist it looks for
    a tool.gvit section in the pyproject.toml.

    The structure in the .gvit.toml file is as follows:
    ---------
    [gvit]
    python = "3.11"
    deps_path = "requirements.txt"
    ---------

    The structure in the pyproject.toml file is as follows:
    ---------
    [tool.gvit]
    python = "3.11"
    deps_path = "requirements.txt"
    ---------
    """
    config_file_path = Path(repo_path) / REPO_CONFIG_FILE
    if config_file_path.exists():
        return toml.load(config_file_path).get("gvit", {})
    pyproject_path = Path(repo_path) / "pyproject.toml"
    if pyproject_path.exists():
        return toml.load(pyproject_path).get("tool", {}).get("gvit", {})
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Method to save the configuration file."""
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)
    typer.secho(f"\nConfiguration saved -> {CONFIG_FILE}", fg=typer.colors.GREEN)


def get_default_backend(config: dict | None = None) -> str:
    """Function to get the default backend from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("backend", DEFAULT_BACKEND)


def get_default_python(config: dict | None = None) -> str:
    """Function to get the default python version from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("python", DEFAULT_PYTHON)


def get_default_install_deps(config: dict | None = None) -> bool:
    """Function to get the default install_deps from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("install_deps", DEFAULT_INSTALL_DEPS)


def get_default_deps_path(config: dict | None = None) -> str:
    """Function to get the default deps_path from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("deps_path", DEFAULT_DEPS_PATH)


def get_default_activate(config: dict | None = None) -> bool:
    """Function to get the default activate from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("activate", DEFAULT_ACTIVATE)


def get_default_verbose(config: dict | None = None) -> bool:
    """Function to get the default verbose from the config."""
    config = config or load_config()
    return config.get("defaults", {}).get("verbose", DEFAULT_VERBOSE)
