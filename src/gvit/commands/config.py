"""
Module for the "gvit config" command.
"""

from typing import cast

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.options.config import (
    backend_option,
    python_option,
    install_deps_option,
    deps_path_option,
)
from gvit.utils.utils import (
    ensure_local_config_dir,
    load_local_config,
    save_local_config,
    get_default_backend,
    get_default_python,
    get_default_install_deps,
    get_default_deps_path
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.utils.schemas import LocalConfig
from gvit.utils.exceptions import CondaNotFoundError
from gvit.backends.conda import CondaBackend


def config(
    backend: str = backend_option,
    python: str = python_option,
    install_deps: bool = install_deps_option,
    deps_path: str = deps_path_option,
) -> None:
    """
    Configure gvit and generate ~/.config/gvit/config.toml configuration file.

    It defines the defaults options to be used if not provided in the different commands or in the repository config.

    Omitted options will be requested via interactive prompts.
    """
    ensure_local_config_dir()
    config = load_local_config()

    if backend is None:
        backend = typer.prompt(
            f"- Select default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})",
            default=get_default_backend(config),
        ).strip()
    validate_backend(backend)
    conda_path = None
    if backend == "conda":
        conda_backend = CondaBackend()
        conda_path = conda_backend.path
        if not conda_backend.is_available():
            raise CondaNotFoundError(
                "Conda is not installed or could not be found in common installation paths. "
                "You can also specify the path manually in your configuration file under "
                "`backends.conda.path`."
            )

    if python is None:
        python = typer.prompt(
            f"- Select default Python version",
            default=get_default_python(config),
        ).strip()
    validate_python(python)

    if install_deps is None:
        default_install_deps = get_default_install_deps(config)
        install_deps = typer.confirm(
            f"- Enable default install-deps (Y/n)? [{'Y' if default_install_deps else "n"}]",
            default=default_install_deps,
            show_default=False
        )

    if deps_path is None:
        deps_path = typer.prompt(
            f"- Select default dependencies path",
            default=get_default_deps_path(config),
        ).strip()

    config = _get_updated_local_config(backend, python, install_deps, deps_path, conda_path)

    save_local_config(config)


def _get_updated_local_config(
    backend: str, python: str, install_deps: bool, deps_path: str, conda_path: str | None
) -> LocalConfig:
    """Function to build the local configuration file."""
    config = {
        "defaults": {
            "backend": backend,
            "python": python,
            "install_deps": install_deps,
            "deps_path": deps_path
        }
    }
    backends_config = {
        "backends": {
            "conda": {
                "path": conda_path
            }
        }
    } if conda_path else {}
    return cast(LocalConfig, {**config, **backends_config})
