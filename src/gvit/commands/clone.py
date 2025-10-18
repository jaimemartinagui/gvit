"""
Module for the "gvit clone" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.options.clone import (
    target_dir_option,
    backend_option,
    python_option,
    install_deps_option,
    activate_option,
    verbose_option
)
from gvit.utils.utils import (
    load_config,
    get_default_backend,
    get_default_python,
    get_default_install_deps,
    get_default_activate,
    get_default_verbose
)
from gvit.validators import validate_backend, validate_python


def clone(
    repo_url: str,
    target_dir: str = target_dir_option,
    backend: str = backend_option,
    python: str = python_option,
    install_deps: bool = install_deps_option,
    activate: bool = activate_option,
    verbose: bool = verbose_option
) -> None:
    """Clone a repo and create a virtual environment."""
    config = load_config()

    target_dir = target_dir or Path(repo_url).stem

    backend = backend or get_default_backend(config)
    validate_backend(backend)

    python = python or get_default_python(config)
    validate_python(python)

    install_deps = install_deps or get_default_install_deps(config)

    activate = activate or get_default_activate(config)

    verbose = verbose or get_default_verbose(config)

    _git_clone(repo_url, target_dir, verbose)

    _create_virtual_env(target_dir, backend, python, verbose)

    if install_deps:
        _install_deps()

    if activate:
        _activate_virtual_env(target_dir, backend, verbose)


def _git_clone(repo_url: str, target_dir: str, verbose: bool) -> None:
    """Function to clone the repository."""
    typer.echo(f"- Cloning repository: {repo_url}...")
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        typer.secho(f"\nGit clone failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Repository was cloned!", fg=typer.colors.GREEN)


def _create_virtual_env(virtual_env_name: str, backend: str, python: str, verbose: bool) -> None:
    """Function to create the virtual environment for the repository."""
    typer.echo(f"\n- Creating virtual environment ({backend} - Python {python}): {virtual_env_name}...")
    if backend == "conda":
        _create_conda_env(virtual_env_name, python, verbose)
    typer.secho(f"Virtual environment was created!", fg=typer.colors.GREEN)


def _install_deps() -> None:
    """Function to install the dependencies in the virtual environment."""
    pass


def _activate_virtual_env(virtual_env_name: str, backend: str, verbose: bool) -> None:
    """Function to activate the virtual environment."""
    typer.echo("\n- Activating virtual environment...")
    if backend == "conda":
        _activate_conda_env(virtual_env_name, verbose)
    typer.secho(f"Virtual environment was activated!", fg=typer.colors.GREEN)


def _create_conda_env(virtual_env_name: str, python: str, verbose: bool) -> None:
    """Function to create the virtual environment using conda."""
    try:
        result = subprocess.run(
            ["conda", "create", "--name", virtual_env_name, f"python={python}", "--yes"],
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Conda environment creation failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _activate_conda_env(virtual_env_name: str, verbose: bool) -> None:
    """Function to activate the conda virtual environment."""
    try:
        result = subprocess.run(
            ["conda", "activate", virtual_env_name],
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Conda environment activation failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
