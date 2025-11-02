"""
Module with common functions for different commands.
"""

from pathlib import Path

import typer

from gvit.backends.conda import CondaBackend
from gvit.backends.venv import VenvBackend
from gvit.backends.virtualenv import VirtualenvBackend
from gvit.utils.schemas import LocalConfig, RepoConfig
from gvit.utils.utils import get_base_deps, get_extra_deps
from gvit.utils.globals import DEFAULT_VENV_NAME


def create_venv(
    venv_name: str | None, repo_path: str, backend: str, python: str, force: bool, verbose: bool
) -> tuple[str, str, str]:
    """
    Create virtual environment for the repository.

    Returns:
        tuple: (registry_name, venv_name, venv_path)
            - registry_name: unique name for registry file
            - venv_name: name of the environment (it can be the same as registry_name or not)
            - venv_path: absolute path to the environment directory
    """
    typer.echo(f'\n- Creating virtual environment {backend} - Python {python}', nl=False)
    typer.secho(" (this might take some time)", nl=False, fg=typer.colors.BLUE)
    typer.echo("...", nl=False)

    repo_path_ = Path(repo_path)

    if backend == "conda":
        venv_name = venv_name or repo_path_.name
        conda_backend = CondaBackend()
        venv_name = conda_backend.create_venv(venv_name, python, force, verbose)
        registry_name = venv_name
        venv_path = conda_backend.get_venv_path(venv_name)
    elif backend == "venv":
        venv_name = venv_name or DEFAULT_VENV_NAME
        venv_backend = VenvBackend()
        venv_name = venv_backend.create_venv(venv_name, repo_path_, python, force, verbose)
        registry_name = venv_backend.generate_unique_venv_registry_name(repo_path_ / venv_name)
        venv_path = venv_backend.get_venv_path(venv_name, repo_path_)
    elif backend == "virtualenv":
        venv_name = venv_name or DEFAULT_VENV_NAME
        virtualenv_backend = VirtualenvBackend()
        venv_name = virtualenv_backend.create_venv(venv_name, repo_path_, python, force, verbose)
        registry_name = virtualenv_backend.generate_unique_venv_registry_name(repo_path_ / venv_name)
        venv_path = virtualenv_backend.get_venv_path(venv_name, repo_path_)
    else:
        raise Exception(f'Backend "{backend}" not supported.')

    typer.echo("✅")
    return registry_name, venv_name, venv_path


def delete_venv(
    backend: str, venv_name: str, venv_path: str, repo_path: Path, verbose: bool = False
) -> None:
    """Function to delete a virtual environment."""
    typer.echo(f'\n- Deleting environment "{venv_name}" backend...', nl=False)
    if backend == "conda":
        conda_backend = CondaBackend()
        conda_backend.delete_venv(venv_name, verbose)
    elif backend == "venv":
        venv_backend = VenvBackend()
        venv_backend.delete_venv(Path(venv_path).name, repo_path, verbose)
    elif backend == "virtualenv":
        virtualenv_backend = VirtualenvBackend()
        virtualenv_backend.delete_venv(Path(venv_path).name, repo_path, verbose)
    typer.echo("✅")


def install_dependencies(
    venv_name: str,
    backend: str,
    repo_path: str,
    base_deps: str | None,
    extra_deps: str | None,
    repo_config: RepoConfig,
    local_config: LocalConfig,
    verbose: bool = False
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
        typer.echo("\n- Installing project and dependencies", nl=False)
        typer.secho(" (this might take some time)", nl=False, fg=typer.colors.BLUE)
        typer.echo("...")
        deps_group_name = f"_base (extras: {extra_deps})" if extra_deps else "_base"
        success = install_dependencies_from_file(
            venv_name=venv_name,
            backend=backend,
            repo_path=repo_path,
            deps_group_name=deps_group_name,
            deps_path=resolved_base,
            extra_deps=extra_deps_,
            verbose=verbose
        )
        return (
            resolved_base if success else None,
            {extra_dep: "pyproject.toml" for extra_dep in extra_deps_} if extra_deps_ else {}
        )

    resolved_extras = _resolve_extra_deps(extra_deps, repo_config, local_config)
    deps_to_install = {**{"_base": resolved_base}, **resolved_extras}
    typer.echo(f"  Dependencies to install: {deps_to_install}")
    typer.echo("\n- Installing dependencies", nl=False)
    typer.secho(" (this might take some time)", nl=False, fg=typer.colors.BLUE)
    typer.echo("...")
    base_sucess = install_dependencies_from_file(
        venv_name=venv_name,
        backend=backend,
        repo_path=repo_path,
        deps_group_name="_base",
        deps_path=resolved_base,
        verbose=verbose
    )
    for deps_group_name, deps_path in resolved_extras.items():
        deps_group_sucess = install_dependencies_from_file(
            venv_name=venv_name,
            backend=backend,
            repo_path=repo_path,
            deps_group_name=deps_group_name,
            deps_path=deps_path, verbose=verbose
        )
        if not deps_group_sucess:
            resolved_extras.pop(deps_group_name)

    return resolved_base if base_sucess else None, resolved_extras


def show_summary_message(registry_name: str, repo_path: Path, venv_path: Path, backend: str) -> None:
    """Function to show the summary message of the process."""
    venv_name = venv_path.name
    if backend == 'conda':
        conda_backend = CondaBackend()
        activate_cmd = conda_backend.get_activate_cmd(venv_name)
    elif backend == 'venv':
        venv_backend = VenvBackend()
        activate_cmd = venv_backend.get_activate_cmd(str(venv_path))
    elif backend == 'virtualenv':
        virtualenv_backend = VirtualenvBackend()
        activate_cmd = virtualenv_backend.get_activate_cmd(str(venv_path))
    else:
        activate_cmd = "# Activation command not available"

    typer.echo("\n🎉  Project setup complete!")
    typer.echo(f"📁  Repository -> {repo_path.name} ({str(repo_path)})")
    typer.echo(f"🐍  Environment [{backend}] -> {venv_name} ({str(venv_path)})")
    typer.echo(f"📖  Registry -> {registry_name} (~/.config/gvit/envs/{registry_name}.toml)")
    typer.echo("🚀  Ready to start working -> ", nl=False)
    typer.secho(f'cd {str(repo_path)} && {activate_cmd}', fg=typer.colors.YELLOW, bold=True)


def get_freeze(venv_name: str, repo_path: Path, repo_url: str, backend: str) -> str | None:
    """Function to get the complete pip freeze output for the environment."""
    if backend == "conda":
        conda_backend = CondaBackend()
        return conda_backend.get_freeze(venv_name, repo_url)
    elif backend == "venv":
        venv_backend = VenvBackend()
        return venv_backend.get_freeze(venv_name, repo_path, repo_url)
    elif backend == "virtualenv":
        virtualenv_backend = VirtualenvBackend()
        return virtualenv_backend.get_freeze(venv_name, repo_path, repo_url)
    return None


def get_freeze_hash(venv_name: str, repo_path: Path, repo_url: str, backend: str) -> str | None:
    """Function to get the pip freeze hash for the environment."""
    if backend == "conda":
        conda_backend = CondaBackend()
        return conda_backend.get_freeze_hash(venv_name, repo_url)
    elif backend == "venv":
        venv_backend = VenvBackend()
        return venv_backend.get_freeze_hash(venv_name, repo_path, repo_url)
    elif backend == "virtualenv":
        virtualenv_backend = VirtualenvBackend()
        return virtualenv_backend.get_freeze_hash(venv_name, repo_path, repo_url)
    return None


def install_dependencies_from_file(
    venv_name: str,
    backend: str,
    repo_path: str,
    deps_group_name: str,
    deps_path: str,
    extra_deps: list[str] | None = None,
    verbose: bool = False
) -> bool:
    """Install dependencies from a single file."""
    repo_path_ = Path(repo_path).resolve()
    deps_path_ = Path(deps_path)
    deps_abs_path = deps_path_ if deps_path_.is_absolute() else repo_path_ / deps_path_

    if backend == "conda":
        conda_backend = CondaBackend()
        return conda_backend.install_dependencies(
            venv_name=venv_name,
            repo_path=repo_path_,
            deps_group_name=deps_group_name,
            deps_path=deps_abs_path,
            extras=extra_deps,
            verbose=verbose
        )
    elif backend == "venv":
        venv_backend = VenvBackend()
        return venv_backend.install_dependencies(
            venv_name=venv_name,
            repo_path=repo_path_,
            deps_group_name=deps_group_name,
            deps_path=deps_abs_path,
            extras=extra_deps,
            verbose=verbose
        )
    elif backend == "virtualenv":
        virtualenv_backend = VirtualenvBackend()
        return virtualenv_backend.install_dependencies(
            venv_name=venv_name,
            repo_path=repo_path_,
            deps_group_name=deps_group_name,
            deps_path=deps_abs_path,
            extras=extra_deps,
            verbose=verbose
        )

    return False


def get_freeze_diff(
    stored_freeze: str, current_freeze: str
) -> tuple[dict[str, str], dict[str, str], dict[str, tuple[str, str]]]:
    """Get the added, removed and modified packages."""
    def parse_freeze(text: str) -> dict[str, str]:
        """Convert a pip freeze text into a {package: version} dict."""
        packages = {}
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                packages[pkg.lower()] = ver
            else:
                # handle non-standard lines (like editable installs or VCS)
                packages[line.lower()] = None
        return packages

    old = parse_freeze(stored_freeze)
    new = parse_freeze(current_freeze)

    added = {pkg: new[pkg] for pkg in new.keys() - old.keys()}
    removed = {pkg: old[pkg] for pkg in old.keys() - new.keys()}
    changed = {pkg: (old[pkg], new[pkg]) for pkg in old.keys() & new.keys() if old[pkg] != new[pkg]}

    return added, removed, changed


def show_freeze_diff(added: dict[str, str], removed: dict[str, str], changed: dict[str, tuple[str, str]]) -> None:
    """Show summary of package changes between two pip freeze outputs."""
    if added:
        typer.echo("  📦 Added packages:")
        for pkg, ver in sorted(added.items()):
            typer.secho(f"    + {pkg}=={ver}" if ver else f"  + {pkg}", fg=typer.colors.GREEN)
        typer.echo()

    if removed:
        typer.echo("  📦 Removed packages:")
        for pkg, ver in sorted(removed.items()):
            typer.secho(f"    - {pkg}=={ver}" if ver else f"  - {pkg}", fg=typer.colors.RED)
        typer.echo()

    if changed:
        typer.echo("  📦 Package versions changed:")
        for pkg, (old_v, new_v) in sorted(changed.items()):
            typer.secho(f"    ~ {pkg}: {old_v} → {new_v}", fg=typer.colors.YELLOW)
        typer.echo()

    if not (added or removed or changed):
        typer.secho("  ✅ No changes detected.", fg=typer.colors.GREEN)
        typer.secho("  Environment is in sync with tracked state.", dim=True)
    else:
        total_changes = len(added) + len(removed) + len(changed)
        typer.secho(f"  Total changes: {total_changes}", fg=typer.colors.BRIGHT_BLACK)


def _resolve_base_deps(base_deps: str | None, repo_config: RepoConfig, local_config: LocalConfig) -> str:
    """Resolve base dependencies."""
    return base_deps or repo_config.get("deps", {}).get("_base") or get_base_deps(local_config)


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
