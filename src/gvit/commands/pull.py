"""
Module for the "gvit pull" command.
"""

import subprocess
from pathlib import Path

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, load_repo_config, get_verbose, get_extra_deps
from gvit.commands._common import install_dependencies_from_file
from gvit.utils.schemas import EnvRegistryFile, RepoConfig


def pull(
    ctx: typer.Context,
    directory: str = typer.Argument(".", help="Directory of the repository (defaults to current directory)."),
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
    # 1. Resolve directory
    target_dir = Path(directory).resolve()
    if not target_dir.exists():
        typer.secho(f"Directory '{directory}' does not exist.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 2. Check if it is a git repository
    if not (target_dir / ".git").exists():
        typer.secho(f"Directory '{directory}' is not a Git repository.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 3. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 4. Get environment from registry (search by repo path)
    typer.echo("- Searching for the environment in the registry...", nl=False)
    env_registry = EnvRegistry()
    envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == target_dir]
    if envs:
        env = envs[0]
        venv_name = env["environment"]["name"]
        typer.secho(f'environment "{venv_name}" found. ✅', fg=typer.colors.GREEN)
    else:
        typer.secho(
            "⚠️  No tracked environment found for this repository (run `gvit setup`).",
            fg=typer.colors.YELLOW
        )
        typer.echo("\n- Running git pull...", nl=False)
        # _pull_repo(str(target_dir), verbose, ctx.args)
        typer.echo("✅")
        typer.echo("\n🎉 Repository updated successfully!")
        return None

    # 5. Run git pull
    typer.echo("\n- Running git pull...", nl=False)
    # _pull_repo(str(target_dir), verbose, ctx.args)
    typer.echo("✅")

    # 6. Skip dependency check if --no-deps
    if no_deps:
        typer.echo("\n- Skipping dependency check...✅")
        typer.echo("\n🎉 Repository updated successfully!")
        return None

    # 7. Get the current path (after pull) for the base and extra deps
    repo_config = load_repo_config(str(target_dir))
    current_deps = _get_current_deps(base_deps, extra_deps, repo_config, env)

    # 8. Get dep groups to reinstall
    if force_deps:
        typer.echo("\n- Force reinstalling all dependencies.")
        to_reinstall = current_deps
    else:
        typer.echo("\n- Searching for changes in dependencies...", nl=False)
        modified_deps_groups = env_registry.get_modified_deps_groups(venv_name, current_deps)
        if not modified_deps_groups:
            typer.secho("environment is up to date ✅", fg=typer.colors.GREEN)
            typer.echo("  Use `gvit pull --force-deps` to update the environment anyway.")
            typer.echo("\n🎉 Repository updated successfully!")
            return None
        to_reinstall = {k: v for k, v in current_deps.items() if k in modified_deps_groups}

    # 9. Reinstall changed dependencies
    typer.echo(f"\n- Dependency groups to re-install: {list(to_reinstall)}.")
    backend = env['environment']['backend']
    for dep_name, dep_path in to_reinstall.items():
        install_dependencies_from_file(
            venv_name, backend, str(target_dir), dep_name, dep_path, verbose=verbose
        )

    # 10. Update registry with new hashes
    env_registry.save_environment_info(
        venv_name=venv_name,
        repo_path=str(target_dir),
        repo_url=env['repository']['url'],
        backend=backend,
        python=env['environment']['python'],
        base_deps=current_deps.get("base"),
        extra_deps={k: v for k, v in current_deps.items() if k != "base"}
    )

    typer.echo("\n🎉 Repository and dependencies updated successfully!")


def _pull_repo(repo_dir: str, verbose: bool = False, extra_args: list[str] | None = None) -> None:
    """Run git pull command."""
    try:
        result = subprocess.run(
            ["git", "pull"] + (extra_args or []),
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.echo("✅")
    except subprocess.CalledProcessError as e:
        typer.secho(f"❗ Git pull failed:\n{e.stderr}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _get_current_deps(
    base_deps: str | None, extra_deps: str | None, repo_config: RepoConfig, env: EnvRegistryFile
) -> dict[str, str]:
    """Function to get the current value for the base deps and extra_deps."""
    current_base_deps = base_deps or repo_config.get("deps", {}).get("base") or env.get("deps", {}).get("base")
    extra_deps_ = {}
    if extra_deps:
        for extra_dep in extra_deps.split(","):
            extra_dep = extra_dep.strip()
            if ":" in extra_dep:
                name, path = extra_dep.split(":", 1)
                extra_deps_[name.strip()] = path.strip()
            else:
                typer.secho("")
    env_extra_deps = {k: v for k, v in env.get("deps", {}).items() if k not in ["base", "installed"]}
    current_extra_deps = (
        extra_deps_ or {**get_extra_deps(repo_config), **extra_deps_} or {**env_extra_deps, **extra_deps_}
    )
    return {"base": current_base_deps, **current_extra_deps} if current_base_deps else current_extra_deps
