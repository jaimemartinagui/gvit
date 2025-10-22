"""
Module for the "gvit clone" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.utils.utils import (
    load_local_config,
    load_repo_config,
    get_backend,
    get_python,
    get_base_deps,
    get_extra_deps,
    get_verbose,
    extract_repo_name_from_url,
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.backends.conda import CondaBackend
from gvit.utils.globals import SUPPORTED_BACKENDS
from gvit.utils.schemas import LocalConfig, RepoConfig


def clone(
    ctx: typer.Context,
    repo_url: str = typer.Argument(help="Repository URL."),
    target_dir: str = typer.Option(None, "--target-dir", "-t", help="Directory to clone into."),
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment to create. If not provided it will take it from the repository name."),
    backend: str = typer.Option(None, "--backend", "-b", help=f"Virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})."),
    python: str = typer.Option(None, "--python", "-p", help="Python version for the virtual environment."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Path to base dependencies file (overrides repo/local config)."),
    extra_deps: str = typer.Option(None, "--extra-deps", help="Extra dependency groups (e.g. 'dev,test' or 'dev:path.txt,test:path2.txt')."),
    no_deps: bool = typer.Option(False, "--no-deps", is_flag=True, help="Skip dependency installation."),
    force: bool = typer.Option(False, "--force", "-f", is_flag=True, help="Overwrite existing environment without confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Clone a repository and create a virtual environment.

    Any extra options will be passed directly to the `git clone` command.

    Long options do not conflict between `gvit clone` and `git clone`.

    Short options might conflict; in that case, use the long form for the `git clone` options.
    """

    # 1. Load the local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 2. Clone the repo
    target_dir = target_dir or extract_repo_name_from_url(repo_url)
    _clone_repo(repo_url, target_dir, verbose, ctx.args)

    # 3. Load the repo config
    repo_config = load_repo_config(target_dir)

    # 4. Create the virtual environment
    venv_name = venv_name or Path(target_dir).stem
    backend = backend or get_backend(local_config)
    python = python or repo_config.get("gvit", {}).get("python") or get_python(local_config)
    validate_backend(backend)
    validate_python(python)
    venv_name = _create_venv(venv_name, backend, python, force, verbose)

    # 5. Install dependencies
    if no_deps:
        typer.echo("\n- Skipping dependency installation...")
    else:
        _install_dependencies(venv_name, backend, target_dir, base_deps, extra_deps, repo_config, local_config, verbose)

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
        typer.echo("✅")
    except subprocess.CalledProcessError as e:
        typer.secho(f"\nGit clone failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _create_venv(venv_name: str, backend: str, python: str, force: bool, verbose: bool) -> str:
    """Function to create the virtual environment for the repository."""
    typer.echo(f'\n- Creating virtual environment "{venv_name}" ({backend} - Python {python})...', nl=False)
    if backend == "conda":
        conda_backend = CondaBackend()
        venv_name = conda_backend.create_venv(venv_name, python, force, verbose)
    typer.echo("✅")
    return venv_name


def _install_dependencies(
    venv_name: str,
    backend: str,
    project_dir: str,
    base_deps: str | None,
    extra_deps: str | None,
    repo_config: RepoConfig,
    local_config: LocalConfig,
    verbose: bool
) -> None:
    """
    Install dependencies with priority resolution system.
    Priority: CLI > Repo Config > Local Config > Default
    """
    typer.echo("\n- Resolving dependencies...")
    base_deps = _resolve_base_deps(base_deps, repo_config, local_config)

    if "pyproject.toml" in base_deps:
        extra_deps_ = extra_deps.split(",") if extra_deps else None
        typer.echo(f'  Dependencies to install: pyproject.toml{f" (extras: {extra_deps})" if extra_deps else ""}')
        typer.echo("\n- Installing project and dependencies...")
        deps_group_name = f"base (extras: {extra_deps})" if extra_deps else "base"
        _install_dependencies_from_file(venv_name, backend, project_dir, deps_group_name, base_deps, extra_deps_, verbose)
        return None

    extra_deps_ = _resolve_extra_deps(extra_deps, repo_config, local_config)
    deps_to_install = {**{"base": base_deps}, **extra_deps_}
    typer.echo(f"  Dependencies to install: {deps_to_install}")
    typer.echo("\n- Installing dependencies...")
    _install_dependencies_from_file(venv_name, backend, project_dir, "base", base_deps, verbose=verbose)
    for deps_group_name, deps_path in extra_deps_.items():
        _install_dependencies_from_file(venv_name, backend, project_dir, deps_group_name, deps_path, verbose=verbose)


def _resolve_base_deps(base_deps: str | None, repo_config: RepoConfig, local_config: LocalConfig) -> str:
    """Resolve base dependencies."""
    return base_deps or repo_config.get("deps", {}).get("base") or get_base_deps(local_config)


def _resolve_extra_deps(
    extra_deps: str | None, repo_config: RepoConfig, local_config: LocalConfig
) -> dict[str, str]:
    """
    Resolve extra dependencies.
    Format: 'dev,test' (names) or 'dev:path1.txt,test:path2.txt' (inline paths)
    Returns dict of {name: path}
    """
    if not extra_deps:
        return {}

    repo_extra_deps = get_extra_deps(repo_config)
    local_extra_deps = get_extra_deps(local_config)

    extras = {}

    for item in extra_deps.split(","):
        item = item.strip()
        if ":" in item:
            # Inline format: "dev:requirements-dev.txt"
            name, path = item.split(":", 1)
            extras[name.strip()] = path.strip()
        else:
            if path := (repo_extra_deps.get(item) or local_extra_deps.get(item)):
                extras[item] = path
            else:
                typer.secho(f'  ⚠️  Extra deps group "{item}" not found in configs, skipping.', fg=typer.colors.YELLOW)

    return extras


def _install_dependencies_from_file(
    venv_name: str,
    backend: str,
    project_dir: str,
    deps_group_name: str,
    deps_path: str,
    extra_deps: list[str] | None = None,
    verbose: bool = False
) -> None:
    """Install dependencies from a single file."""
    project_path = Path(project_dir).resolve()
    deps_path_ = Path(deps_path)
    deps_abs_path = deps_path_ if deps_path_.is_absolute() else project_path / deps_path_
    if backend == "conda":
        conda_backend = CondaBackend()
        conda_backend.install_dependencies(venv_name, deps_group_name, deps_abs_path, project_path, extra_deps, verbose)


def _show_summary_message(venv_name: str, backend: str, project_dir: str) -> None:
    """Function to show the summary message of the process."""
    if backend == 'conda':
        conda_backend = CondaBackend()
        activate_cmd = conda_backend.get_activate_cmd(venv_name)
    typer.echo("\n🎉  Project setup complete!")
    typer.echo(f"📁  Repository -> {project_dir}")
    typer.echo(f"🐍  Environment ({backend}) -> {venv_name}")
    typer.echo("🚀  Ready to start working -> ", nl=False)
    typer.secho(f'cd {project_dir} && {activate_cmd}', fg=typer.colors.YELLOW, bold=True)
