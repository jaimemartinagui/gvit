"""
Module for the "gvit clone" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.options.clone import (
    target_dir_option,
    venv_name_option,
    backend_option,
    python_option,
    install_deps_option,
    deps_path_option,
    force_option,
    verbose_option,
)
from gvit.utils.utils import (
    load_local_config,
    load_repo_config,
    get_default_backend,
    get_default_python,
    get_default_install_deps,
    get_default_deps_path,
    get_default_verbose,
    extract_repo_name_from_url,
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.backends.conda import CondaBackend


def clone(
    ctx: typer.Context,
    repo_url: str,
    target_dir: str = target_dir_option,
    venv_name: str = venv_name_option,
    backend: str = backend_option,
    python: str = python_option,
    install_deps: bool = install_deps_option,
    deps_path: str = deps_path_option,
    force: bool = force_option,
    verbose: bool = verbose_option,
) -> None:
    """
    Clone a repository and create a virtual environment.

    Any extra options will be passed directly to the `git clone` command.

    Long options do not conflict between `gvit clone` and `git clone`.

    Short options might conflict; in that case, use the long form for the `git clone` options.
    """

    # 1. Load the local config
    local_config = load_local_config()
    verbose = verbose or get_default_verbose(local_config)

    # 2. Clone the repo
    target_dir = target_dir or extract_repo_name_from_url(repo_url)
    _clone_repo(repo_url, target_dir, verbose, ctx.args)

    # 3. Load the repo config
    repo_config = load_repo_config(target_dir)

    # 4. Create the virtual environment
    venv_name = venv_name or Path(target_dir).stem
    backend = backend or get_default_backend(local_config)
    python = python or repo_config.get("gvit", {}).get("python") or get_default_python(local_config)
    validate_backend(backend)
    validate_python(python)
    venv_name = _create_venv(venv_name, backend, python, force, verbose)

    # 5. Install dependencies
    install_deps = install_deps or get_default_install_deps(local_config)
    if install_deps:
        deps_path = deps_path or repo_config.get("gvit", {}).get("deps_path") or get_default_deps_path(local_config)
        _install_deps(venv_name, backend, deps_path, target_dir, verbose)

    # 6. Summary message
    _show_summary_message(venv_name, backend, target_dir)


def _clone_repo(repo_url: str, target_dir: str, verbose: bool, extra_args: list[str] | None = None) -> None:
    """Function to clone the repository."""
    typer.echo(f"- Cloning repository {repo_url}...", nl=False)
    try:
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
    typer.secho(f"repository was cloned!", fg=typer.colors.GREEN)


def _create_venv(venv_name: str, backend: str, python: str, force: bool, verbose: bool) -> str:
    """Function to create the virtual environment for the repository."""
    typer.echo(f'\n- Creating virtual environment "{venv_name}" ({backend} - Python {python})...', nl=False)
    if backend == "conda":
        conda_backend = CondaBackend()
        venv_name = conda_backend.create_venv(venv_name, python, force, verbose)
    typer.secho(f"virtual environment was created!", fg=typer.colors.GREEN)
    return venv_name


def _install_deps(
    venv_name: str, backend: str, deps_path: str, target_dir: str, verbose: bool
) -> None:
    """Function to install the dependencies in the virtual environment."""
    typer.echo("\n- Installing dependencies...", nl=False)
    deps_abs_path = Path(target_dir).resolve() / deps_path
    if not deps_abs_path.exists():
        typer.secho("Dependencies could not be retrieved!", fg=typer.colors.RED)
        return None
    if backend == "conda":
        conda_backend = CondaBackend()
        conda_backend.install_deps(venv_name, str(deps_abs_path), verbose)
    typer.secho(f"dependencies were installed!", fg=typer.colors.GREEN)


def _show_summary_message(venv_name: str, backend: str, target_dir: str) -> None:
    """Function to show the summary message of the process."""
    if backend == 'conda':
        conda_backend = CondaBackend()
        activate_cmd = conda_backend.get_activate_cmd(venv_name)
    combined_cmd = f'cd {target_dir} && {activate_cmd}'
    typer.echo("\n🎉  Project setup complete!")
    typer.echo(f"📁  Repository -> {target_dir}")
    typer.echo(f"🐍  Environment ({backend}) -> {venv_name}")
    typer.echo("🚀  Ready to start working -> ", nl=False)
    typer.secho(f"{combined_cmd}", fg=typer.colors.YELLOW, bold=True)
