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
    deps_path_option,
    verbose_option
)
from gvit.utils.utils import (
    load_config,
    load_repo_config,
    get_default_backend,
    get_default_python,
    get_default_install_deps,
    get_default_deps_path,
    get_default_verbose
)
from gvit.utils.validators import validate_backend, validate_python


def clone(
    ctx: typer.Context,
    repo_url: str,
    target_dir: str = target_dir_option,
    backend: str = backend_option,
    python: str = python_option,
    install_deps: bool = install_deps_option,
    deps_path: str = deps_path_option,
    verbose: bool = verbose_option
) -> None:
    """
    Clone a repository and create a virtual environment.

    Any extra options will be passed directly to the `git clone` command.

    Long options do not conflict between `gvit clone` and `git clone`.

    Short options might conflict; in that case, use the long form for the `git clone` options.
    """

    # 1. Load the user config
    config = load_config()
    verbose = verbose or get_default_verbose(config)

    # 2. Clone the repo
    target_dir = target_dir or Path(repo_url).stem
    _git_clone(repo_url, target_dir, verbose, ctx.args)

    # 3. Load the repo config
    repo_config = load_repo_config(target_dir)

    # 4. Create the virtual environment
    virtual_env_name = Path(target_dir).stem
    backend = backend or get_default_backend(config)
    python = python or repo_config.get("python") or get_default_python(config)
    validate_backend(backend)
    validate_python(python)
    _create_virtual_env(virtual_env_name, backend, python, verbose)

    # 5. Install dependencies
    install_deps = install_deps or get_default_install_deps(config)
    if install_deps:
        deps_path = deps_path or repo_config.get("deps_path") or get_default_deps_path(config)
        _install_deps(virtual_env_name, backend, deps_path, target_dir, verbose)

    # 6. Show message to activate the environment
    _show_activate_message(virtual_env_name, backend)


def _git_clone(repo_url: str, target_dir: str, verbose: bool, extra_args: list[str] | None = None) -> None:
    """Function to clone the repository."""
    typer.echo(f"- Cloning repository -> {repo_url}...")
    try:
        cmd = ["git", "clone", repo_url, target_dir] + (extra_args or [])
        print(cmd)
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir] + (extra_args or []),
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
    typer.echo(f"\n- Creating virtual environment ({backend} - Python {python}) -> {virtual_env_name}...")
    if backend == "conda":
        _create_conda_env(virtual_env_name, python, verbose)
    typer.secho(f"Virtual environment was created!", fg=typer.colors.GREEN)


def _install_deps(
    virtual_env_name: str, backend: str, deps_path: str, target_dir: str, verbose: bool
) -> None:
    """Function to install the dependencies in the virtual environment."""
    typer.echo("\n- Installing dependencies...")
    deps_abs_path = Path(target_dir).resolve() / deps_path
    if not deps_abs_path.exists():
        typer.secho("Dependencies could not be retrieved!", fg=typer.colors.RED)
        return None
    if backend == "conda":
        _install_deps_conda_env(virtual_env_name, str(deps_abs_path), verbose)
    typer.secho(f"Dependencies were installed!", fg=typer.colors.GREEN)


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
        typer.secho(f"Failed to create conda environment:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _install_deps_conda_env(virtual_env_name: str, deps_path: str, verbose: bool) -> None:
    """Function to install the dependencies in the conda environment."""
    if "requirements.txt" in deps_path:
        deps_install_command = ["pip", "install", "-r", deps_path]
    elif "pyproject.toml" in deps_path:
        deps_install_command = ["pip", "install", "-e", deps_path]
    else:
        raise Exception("Only requirements.txt and pyporject.toml are supported!")

    try:
        result = subprocess.run(
            ["conda", "run", "-n", virtual_env_name] + deps_install_command,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Failed to install dependencies to conda environment:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _show_activate_message(virtual_env_name: str, backend: str) -> None:
    """Function to show the command to activate the environment."""
    typer.echo("\n- Activate virtual environment with the following command -> ", nl=False)
    if backend == "conda":
        typer.secho(f"conda activate {virtual_env_name}", fg=typer.colors.YELLOW)
