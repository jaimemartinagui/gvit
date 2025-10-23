"""
Module with common functions for different commands.
"""

from pathlib import Path

import typer

from gvit.backends.conda import CondaBackend
from gvit.utils.schemas import LocalConfig, RepoConfig
from gvit.utils.utils import get_base_deps, get_extra_deps


def create_venv(venv_name: str, backend: str, python: str, force: bool, verbose: bool) -> str:
    """Function to create the virtual environment for the repository."""
    typer.echo(f'\n- Creating virtual environment "{venv_name}" - {backend} - Python {python}', nl=False)
    typer.secho(" (this might take some time)", nl=False, fg=typer.colors.BLUE)
    typer.echo("...", nl=False)
    if backend == "conda":
        conda_backend = CondaBackend()
        venv_name = conda_backend.create_venv(venv_name, python, force, verbose)
    typer.echo("✅")
    return venv_name


def install_dependencies(
    venv_name: str,
    backend: str,
    project_dir: str,
    base_deps: str | None,
    extra_deps: str | None,
    repo_config: RepoConfig,
    local_config: LocalConfig,
    verbose: bool
) -> tuple[str | None, dict[str, str]]:
    """
    Install dependencies with priority resolution system.
    Priority: CLI > Repo Config > Local Config > Default
    """
    typer.echo("\n- Resolving dependencies...")
    resolved_base = _resolve_base_deps(base_deps, repo_config, local_config)

    if "pyproject.toml" in resolved_base:
        extra_deps_ = extra_deps.split(",") if extra_deps else None
        typer.echo(f'  Dependencies to install: pyproject.toml{f" (extras: {extra_deps})" if extra_deps else ""}')
        typer.echo("\n- Installing project and dependencies...")
        deps_group_name = f"base (extras: {extra_deps})" if extra_deps else "base"
        success = _install_dependencies_from_file(
            venv_name, backend, project_dir, deps_group_name, resolved_base, extra_deps_, verbose
        )
        return resolved_base if success else None, {}

    resolved_extras = _resolve_extra_deps(extra_deps, repo_config, local_config)
    deps_to_install = {**{"base": resolved_base}, **resolved_extras}
    typer.echo(f"  Dependencies to install: {deps_to_install}")
    typer.echo("\n- Installing dependencies...")
    base_sucess = _install_dependencies_from_file(venv_name, backend, project_dir, "base", resolved_base, verbose=verbose)
    for deps_group_name, deps_path in resolved_extras.items():
        deps_group_sucess = _install_dependencies_from_file(
            venv_name, backend, project_dir, deps_group_name, deps_path, verbose=verbose
        )
        if not deps_group_sucess:
            resolved_extras.pop(deps_group_name)

    return resolved_base if base_sucess else None, resolved_extras


def show_summary_message(venv_name: str, backend: str, project_dir: str) -> None:
    """Function to show the summary message of the process."""
    if backend == 'conda':
        conda_backend = CondaBackend()
        activate_cmd = conda_backend.get_activate_cmd(venv_name)
    typer.echo("\n🎉  Project setup complete!")
    typer.echo(f"📁  Repository -> {project_dir}")
    typer.echo(f"🐍  Environment ({backend}) -> {venv_name}")
    typer.echo(f"📖  Registry updated -> ~/.config/gvit/envs/{venv_name}.toml")
    typer.echo("🚀  Ready to start working -> ", nl=False)
    typer.secho(f'cd {project_dir} && {activate_cmd}', fg=typer.colors.YELLOW, bold=True)


def _install_dependencies_from_file(
    venv_name: str,
    backend: str,
    project_dir: str,
    deps_group_name: str,
    deps_path: str,
    extra_deps: list[str] | None = None,
    verbose: bool = False
) -> bool:
    """Install dependencies from a single file."""
    project_path = Path(project_dir).resolve()
    deps_path_ = Path(deps_path)
    deps_abs_path = deps_path_ if deps_path_.is_absolute() else project_path / deps_path_
    if backend == "conda":
        conda_backend = CondaBackend()
        return conda_backend.install_dependencies(
            venv_name, deps_group_name, deps_abs_path, project_path, extra_deps, verbose
        )
    return False


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
