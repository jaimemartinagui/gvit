"""
Module with utility functions.
"""

from typing import cast
import importlib.metadata
from pathlib import Path

import toml
import typer
from click import Group

from gvit.utils.globals import (
    LOCAL_CONFIG_DIR,
    LOCAL_CONFIG_FILE,
    REPO_CONFIG_FILE,
    DEFAULT_BACKEND,
    DEFAULT_VENV_NAME,
    DEFAULT_PYTHON,
    DEFAULT_PACKAGE_MANAGER,
    DEFAULT_BASE_DEPS,
    DEFAULT_VERBOSE
)
from gvit.utils.schemas import LocalConfig, RepoConfig


def get_app_commands(app: typer.Typer) -> set:
    """Function to get the commands registered in the provided Typer app."""
    click_app = typer.main.get_command(app)
    return set(click_app.commands.keys()) if isinstance(click_app, Group) else set()


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


def ensure_local_config_dir() -> None:
    """Method to create the local configuration folder if necessary."""
    LOCAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_local_config() -> LocalConfig:
    """Method to load the local configuration file."""
    return cast(LocalConfig, toml.load(LOCAL_CONFIG_FILE) if LOCAL_CONFIG_FILE.exists() else {})


def load_repo_config(repo_path: str) -> RepoConfig:
    """
    Method to load the configuration file from the repository.
    It looks for a .gvit.toml file in the root of the repo. If it does not exist it looks for
    a tool.gvit section in the pyproject.toml.
    """
    config_file_path = Path(repo_path) / REPO_CONFIG_FILE
    if config_file_path.exists():
        return cast(RepoConfig, toml.load(config_file_path))
    pyproject_path = Path(repo_path) / "pyproject.toml"
    if pyproject_path.exists():
        return {"gvit": toml.load(pyproject_path).get("tool", {}).get("gvit", {})}
    return {}


def save_local_config(config: LocalConfig) -> None:
    """Method to save the local configuration file."""
    with open(LOCAL_CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def get_backend(config: LocalConfig) -> str:
    """Function to get the backend from the config."""
    return config.get("gvit", {}).get("backend", DEFAULT_BACKEND)


def get_python(config: LocalConfig | RepoConfig) -> str:
    """Function to get the python version from the config."""
    return config.get("gvit", {}).get("python", DEFAULT_PYTHON)


def get_package_manager(config: LocalConfig | RepoConfig) -> str:
    """Function to get the python package manager from the config."""
    return config.get("gvit", {}).get("package_manager", DEFAULT_PACKAGE_MANAGER)


def get_base_deps(config: LocalConfig | RepoConfig) -> str:
    """Function to get the base deps from the config."""
    return config.get("deps", {}).get("_base", DEFAULT_BASE_DEPS)


def get_extra_deps(config: LocalConfig | RepoConfig) -> dict:
    """Function to get the extra deps from the config."""
    deps = config.get("deps")
    return {k: v for k, v in deps.items() if k != "_base"} if deps else {}


def get_verbose(config: LocalConfig) -> bool:
    """Function to get the verbose from the config."""
    return config.get("gvit", {}).get("verbose", DEFAULT_VERBOSE)


def get_venv_name(config: LocalConfig) -> str:
    """Function to get the venv name from the config (for venv backend)."""
    return config.get("backends", {}).get("venv", {}).get("name", DEFAULT_VENV_NAME)


def extract_repo_name_from_url(repo_url: str) -> str:
    """
    Extract repository name from Git URL.
    
    Handles various Git URL formats:
    - https://github.com/user/repo.git -> repo
    - https://github.com/user/repo -> repo
    - git@github.com:user/repo.git -> repo
    - /path/to/local/repo -> repo
    """
    repo_url = repo_url[:-4] if repo_url.endswith('.git') else repo_url
    # Handle SSH format (git@host:user/repo)
    if '@' in repo_url and ':' in repo_url:
        repo_url = repo_url.split(':')[-1]
    return Path(repo_url).name
