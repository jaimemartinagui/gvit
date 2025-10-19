"""
Module for the "gvit config" command.
"""

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.options.config import (
    backend_option,
    python_option,
    install_deps_option,
    deps_path_option,
    activate_option
)
from gvit.utils.utils import (
    ensure_config_dir,
    load_config,
    save_config,
    get_default_backend,
    get_default_python,
    get_default_install_deps,
    get_default_deps_path,
    get_default_activate
)
from gvit.utils.validators import validate_backend, validate_python


def config(
    backend: str = backend_option,
    python: str = python_option,
    install_deps: bool = install_deps_option,
    deps_path: str = deps_path_option,
    activate: bool = activate_option
) -> None:
    """Configure gvit and generate ~/.config/gvit/config.toml configuration file."""
    ensure_config_dir()
    config = load_config()

    if backend is None:
        backend = typer.prompt(
            f"- Select default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})",
            default=get_default_backend(config),
        ).strip()
    validate_backend(backend)

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

    if activate is None:
        default_activate = get_default_activate(config)
        activate = typer.confirm(
            f"- Enable default activate (Y/n)? [{'Y' if default_activate else "n"}]",
            default=default_activate,
            show_default=False
        )

    config["defaults"] = {
        "backend": backend,
        "python": python,
        "install_deps": install_deps,
        "deps_path": deps_path,
        "activate": activate
    }

    save_config(config)
