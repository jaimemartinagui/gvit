"""
Module for the "gvit pull" command.
"""

from pathlib import Path

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, load_repo_config, get_verbose, get_extra_deps, get_package_manager
from gvit.backends.common import install_dependencies
from gvit.utils.schemas import RegistryFile, RepoConfig
from gvit.utils.validators import validate_directory, validate_git_repo, validate_package_manager
from gvit.git import Git
from gvit.utils.globals import SUPPORTED_PACKAGE_MANAGERS


def pull(
    ctx: typer.Context,
    target_dir: str = typer.Option(".", "--target-dir", "-t", help="Directory of the repository (defaults to current directory)."),
    package_manager: str = typer.Option(None, "--package-manager", "-m", help=f"Python package manager ({'/'.join(SUPPORTED_PACKAGE_MANAGERS)})."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Path to base dependencies file (overrides repo/local config)."),
    extra_deps: str = typer.Option(None, "--extra-deps", help="Extra dependency groups (e.g. 'dev,test' or 'dev:path.txt,test:path2.txt')."),
    no_deps: bool = typer.Option(False, "--no-deps", help="Skip dependency reinstallation even if changes detected."),
    force_deps: bool = typer.Option(False, "--force-deps", "-f", help="Force reinstall all dependencies even if no changes detected."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Pull changes from remote repository and update virtual environment if needed.

    Runs `git pull` and then checks if dependency files have changed.
    If changes are detected, automatically reinstalls the affected dependencies.

    Any extra options will be passed directly to `git pull`.
    """
    # 1. Resolve and validate directory
    target_dir_ = Path(target_dir).resolve()
    validate_directory(target_dir_)

    # 2. Check if it is a git repository
    validate_git_repo(target_dir_)

    # 3. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 4. Get environment from registry (search by repo path)
    typer.echo("- Searching for the environment in the registry...", nl=False)
    env_registry = EnvRegistry()
    envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == target_dir_]
    if envs:
        env = envs[0]
        registry_name = env["environment"]["name"]
        venv_name = Path(env["environment"]["path"]).name
        typer.secho(f'environment found: "{registry_name}". ✅', fg=typer.colors.GREEN)
    else:
        env = None
        typer.secho(
            "⚠️  No tracked environment found for this repository (run `gvit setup`).",
            fg=typer.colors.YELLOW
        )

    # 5. Run git pull
    typer.echo("\n- Running git pull...", nl=False)
    Git().pull(str(target_dir_), ctx.args, verbose)

    # 6. Skip dependency check if --no-deps
    if no_deps:
        typer.echo("\n- Skipping dependency check...✅")
    if no_deps or not env:
        typer.echo("\n🎉 Repository updated successfully!")
        return None

    # 7. Get the current path (after pull) for the base and extra deps
    repo_config = load_repo_config(str(target_dir_))
    current_deps = _get_current_deps(base_deps, extra_deps, repo_config, env)
    if not force_deps and not current_deps:
        typer.echo("\n- There are no tracked dependencies.")
        typer.echo("\n🎉 Repository updated successfully!")
        return None

    # 8. Get dep groups to reinstall
    if force_deps:
        typer.echo("\n- Force reinstalling all dependencies.")
        to_reinstall = current_deps
    else:
        typer.echo("\n- Searching for changes in dependencies...", nl=False)
        modified_deps_groups = env_registry.get_modified_deps_groups(registry_name, current_deps)
        to_reinstall = {k: v for k, v in current_deps.items() if k in modified_deps_groups}
        if not to_reinstall:
            typer.secho("environment is up to date ✅", fg=typer.colors.GREEN)
            typer.echo("  Use `gvit pull --force-deps` to update the environment anyway.")
            typer.echo("\n🎉 Repository updated successfully!")
            return None
        typer.echo("✅")

    # 9. Reinstall changed dependencies
    if "_base" not in to_reinstall:
        to_reinstall["_base"] = current_deps["_base"]
    package_manager = package_manager or get_package_manager(local_config)
    validate_package_manager(package_manager)
    # I do not care about the resolved_base_deps and resolved_extra_deps returned by the install_dependencies
    # function because there might be some extra deps which are not reinstalled, so we have to pass to
    # the save_venv_info function the current_deps, to keep track of all the groups, not just the ones
    # that have been modified and, therefore, reinstalled.
    install_dependencies(
        venv_name=venv_name,
        backend=env['environment']['backend'],
        package_manager=package_manager,
        repo_path=str(target_dir_),
        base_deps=to_reinstall["_base"],
        extra_deps=_get_parsed_extra_deps(to_reinstall),
        repo_config=repo_config,
        local_config=local_config,
        verbose=verbose
    )

    # 10. Update registry with new hashes
    env_registry.save_venv_info(
        registry_name=registry_name,
        venv_name=venv_name,
        venv_path=env['environment']['path'],
        repo_path=str(target_dir_),
        repo_url=env['repository']['url'],
        backend=env['environment']['backend'],
        python=env['environment']['python'],
        base_deps=current_deps.get("_base"),
        extra_deps={k: v for k, v in current_deps.items() if k != "_base"}
    )

    typer.echo("\n🎉 Repository and environment updated successfully!")


def _get_parsed_extra_deps(to_reinstall: dict[str, str]) -> str:
    """Function to get the correct extra_deps format for the installation."""
    return (
        ",".join([k for k in to_reinstall if k != "_base"])
        if "pyproject.toml" in to_reinstall["_base"]
        else ",".join(f"{k}:{v}" for k, v in to_reinstall.items() if k != "_base")
    )


def _get_current_deps(
    base_deps: str | None, extra_deps: str | None, repo_config: RepoConfig, env: RegistryFile
) -> dict:
    """
    Function to get the current value for the base deps and extra_deps.
    Priority: CLI > repo_config > env
    """
    current_base_deps = base_deps or repo_config.get("deps", {}).get("_base") or env.get("deps", {}).get("_base")
    repo_extra_deps = get_extra_deps(repo_config)
    env_extra_deps = {k: v for k, v in env.get("deps", {}).items() if k not in ["_base", "installed"]}
    extra_deps_ = {}
    if extra_deps:
        for extra_dep in extra_deps.split(","):
            extra_dep = extra_dep.strip()
            if ":" in extra_dep:
                name, path = extra_dep.split(":", 1)
                extra_deps_[name.strip()] = path.strip()
            else:
                if path := (repo_extra_deps.get(extra_dep) or env_extra_deps.get(extra_dep)):
                    extra_deps_[extra_dep] = path
                else:
                    typer.secho(
                        f'  ⚠️  Extra deps group "{extra_dep}" not found, skipping.',
                        fg=typer.colors.YELLOW
                    )
    current_extra_deps = extra_deps_ or repo_extra_deps or env_extra_deps
    return {"_base": current_base_deps, **current_extra_deps} if current_base_deps else current_extra_deps
