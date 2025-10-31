"""
Module for the "gvit envs" group of commands.
"""

from pathlib import Path

import toml
import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.globals import ENVS_DIR
from gvit.utils.utils import load_local_config, load_repo_config
from gvit.backends.conda import CondaBackend
from gvit.backends.venv import VenvBackend
from gvit.backends.virtualenv import VirtualenvBackend
from gvit.backends.common import create_venv, delete_venv, install_dependencies


def list_() -> None:
    """List the environments tracked in the gvit environment registry."""
    env_registry = EnvRegistry()
    envs = env_registry.get_environments()
    if not envs:
        typer.echo("No environments in registry.")
        return None

    typer.echo("Tracked environments:")
    for env in envs:
        venv_name = env["environment"]["name"]
        venv_path = env["environment"]["path"]
        backend = env["environment"]["backend"]
        python = env["environment"]["python"]
        repo_path = env["repository"]["path"]
        env_registry_file = ENVS_DIR / f"{venv_name}.toml"

        if backend == "conda":
            conda_backend = CondaBackend()
            activate_cmd = conda_backend.get_activate_cmd(venv_name)
        elif backend == "venv":
            venv_backend = VenvBackend()
            activate_cmd = venv_backend.get_activate_cmd(venv_path)
        elif backend == "virtualenv":
            virtualenv_backend = VirtualenvBackend()
            activate_cmd = virtualenv_backend.get_activate_cmd(venv_path)
        else:
            activate_cmd = f"# Activate command for {backend} not available"

        typer.secho(f"\n  • {venv_name}", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"    Backend:       {backend}")
        typer.echo(f"    Python:        {python}")
        typer.echo(f"    Environment:   {venv_path}")
        typer.echo(f"    Repository:    {repo_path}")
        typer.echo(f"    Registry:      {env_registry_file}")
        typer.secho(f"    Command:       ", nl=False, dim=True)
        typer.secho(f"cd {repo_path} && {activate_cmd}", fg=typer.colors.YELLOW)


def delete(
    venv_name: str = typer.Argument(help="Name of the environment to delete (backend and registry)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Remove an environment (backend and registry).
    If the backend deletion fails, do not remove the registry to keep track of it.
    """
    env_registry = EnvRegistry()
    venv_info = env_registry.load_environment_info(venv_name)
    if venv_info is None:
        typer.secho(f'⚠️  Environment "{venv_name}" not found.', fg=typer.colors.YELLOW)
        return None

    delete_venv(
        backend=venv_info["environment"]["backend"],
        venv_name=venv_name,
        venv_path=venv_info["environment"]["path"],
        repo_path=Path(venv_info["repository"]["path"]),
        verbose=verbose
    )

    typer.echo(f'- Removing environment "{venv_name}" registry...', nl=False)
    if env_registry.delete_environment_registry(venv_name):
        typer.echo("✅")
    else:
        typer.secho(f'❗ Registry deletion failed.', fg=typer.colors.RED)
        raise typer.Exit(code=1)


def prune(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without actually removing."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Remove the environments without confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """Remove environments (backend and registry) if their repository path no longer exists."""
    typer.echo("- Checking for orphaned environments...", nl=False)
    env_registry = EnvRegistry()
    orphaned_envs = env_registry.get_orphaned_envs()

    if not orphaned_envs:
        typer.echo("no orphaned environments found")
        return None

    typer.echo(f"found {len(orphaned_envs)} orphaned environment(s):\n")
    for venv_info in orphaned_envs:
        typer.echo(
            f'  • {venv_info["environment"]["name"]} ({venv_info["environment"]["backend"]}) -> {venv_info["repository"]["path"]}'
        )

    if dry_run:
        typer.echo("\n[DRY RUN] No changes made. Run without --dry-run to actually prune.")
        return None

    if not yes and not typer.confirm("\n  Do you want to delete these environments?", default=False):
        typer.secho("  Aborted!", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    errors_registry = []
    errors_backend = []
    for venv_info in orphaned_envs:
        venv_name = venv_info["environment"]["name"]
        typer.echo(f'\n- Pruning "{venv_name}" environment:')

        typer.echo("  Deleting backend...", nl=False)
        backend = venv_info["environment"]["backend"]
        try:
            if backend == "conda":
                conda_backend = CondaBackend()
                if conda_backend.venv_exists(venv_name):
                    conda_backend.delete_venv(venv_name, verbose=verbose)
                    typer.echo("✅")
                else:
                    typer.secho('⚠️  Environment not found in backend', fg=typer.colors.YELLOW)
            elif backend in ["venv", "virtualenv"]:
                typer.secho('⚠️  Repository deleted, environment was already removed', fg=typer.colors.YELLOW)
        except Exception:
            errors_backend.append(venv_name)
            continue

        typer.echo("  Deleting registry...", nl=False)
        if env_registry.delete_environment_registry(venv_name):
            typer.echo("✅")
        else:
            errors_registry.append(venv_name)
            typer.secho("❗ Failed to delete registry", fg=typer.colors.RED)

    pruned_envs = [
        venv_info["environment"]["name"]
        for venv_info in orphaned_envs
        if venv_info["environment"]["name"] not in errors_registry + errors_backend
    ]
    if pruned_envs:
        typer.echo(f"\n🎉 Pruned {len(pruned_envs)} environment(s).")
    if errors_registry:
        typer.secho(f'\n⚠️  Errors on registry deletion: {errors_registry}', fg=typer.colors.YELLOW)
    if errors_backend:
        typer.secho(f'\n⚠️  Errors on backend deletion: {errors_backend}', fg=typer.colors.YELLOW)


def reset(
    venv_name: str = typer.Argument(help="Name of the environment to reset."),
    no_deps: bool = typer.Option(False, "--no-deps", is_flag=True, help="Skip dependency installation."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Reset an environment by recreating it and reinstalling dependencies from registry.

    This command:

    1. Deletes the environment backend.

    2. Recreates it with the same Python version.

    3. Reinstalls dependencies tracked in the registry (unless --no-deps).

    4. Preserves the registry entry (unlike delete + setup).
    """
    registry_name = venv_name
    env_registry = EnvRegistry()
    venv_info = env_registry.load_environment_info(registry_name)

    if venv_info is None:
        typer.secho(f'⚠️  Environment "{registry_name}" not found in registry.', fg=typer.colors.YELLOW)
        return None

    backend = venv_info["environment"]["backend"]
    python = venv_info["environment"]["python"]
    venv_path = venv_info["environment"]["path"]
    repo_path = Path(venv_info["repository"]["path"])
    venv_name = Path(venv_path).name

    if not repo_path.exists():
        typer.secho(f"⚠️  Repository path not found: {repo_path}", fg=typer.colors.YELLOW)
        typer.echo("   Run `gvit envs prune` to clean orphaned environments.")
        return None

    if not yes:
        typer.echo(f'- This will reset environment "{registry_name}":')
        typer.echo(f'  Backend:     {backend}')
        typer.echo(f'  Python:      {python}')
        typer.echo(f'  Path:        {venv_path}')
        typer.echo(f'  Repository:  {repo_path}')
        if not typer.confirm("\n  Continue?", default=False):
            typer.secho("  Aborted!", fg=typer.colors.RED)
            return None

    # 1: Delete backend
    delete_venv(
        backend=backend, venv_name=venv_name, venv_path=venv_path, repo_path=repo_path, verbose=verbose
    )

    # 2: Recreate backend
    _, venv_name, venv_path = create_venv(
        venv_name=venv_name,
        repo_path=str(repo_path),
        backend=backend,
        python=python,
        force=True,
        verbose=verbose
    )

    # 3: Reinstall dependencies (if requested)
    if no_deps:
        typer.echo("\n- Skipping dependency installation...✅")
        # Clear installed section from registry since nothing was installed
        if "deps" in venv_info and "installed" in venv_info.get("deps", {}):
            typer.echo("\n- Clearing dependency tracking from registry...", nl=False)
            venv_info["deps"].pop("installed", None)
            with open(ENVS_DIR / f"{registry_name}.toml", "w") as f:
                toml.dump(venv_info, f)
            typer.echo("✅")
        _show_summary_msg_reset(registry_name)
        return None

    deps = venv_info.get("deps", {})
    if not deps or ("_base" not in deps and len([k for k in deps.keys() if k != "installed"]) == 0):
        typer.echo("\n- No dependencies tracked in registry...✅")
        _show_summary_msg_reset(registry_name)
        return None

    extra_deps = {k: v for k, v in deps.items() if k not in ["_base", "installed"]}
    resolved_base_deps, resolved_extra_deps = install_dependencies(
        venv_name=venv_name,
        backend=backend,
        repo_path=str(repo_path),
        base_deps=deps.get("_base"),
        extra_deps=",".join(extra_deps),
        repo_config=load_repo_config(str(repo_path)),
        local_config=load_local_config(),
        verbose=verbose,
    )

    # 4. Save environment info to registry
    env_registry.save_venv_info(
        registry_name=registry_name,
        venv_name=venv_name,
        venv_path=venv_path,
        repo_path=str(repo_path),
        repo_url=venv_info["repository"]["url"],
        backend=backend,
        python=python,
        base_deps=resolved_base_deps,
        extra_deps=resolved_extra_deps,
        created_at=venv_info["environment"]["created_at"]
    )

    # 5. Summary message
    _show_summary_msg_reset(registry_name)


def show(venv_name: str = typer.Argument(help="Name of the environment to display.")) -> None:
    """Display the environment registry file for a specific environment."""
    env_registry = EnvRegistry()

    if not env_registry.venv_exists_in_registry(venv_name):
        typer.secho(f'Environment "{venv_name}" not found in registry.', fg=typer.colors.YELLOW)
        return None

    env_file = ENVS_DIR / f"{venv_name}.toml"

    typer.secho(f"───────┬────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)
    typer.secho(f"       │ File: {env_file}", fg=typer.colors.BRIGHT_BLACK)
    typer.secho(f"───────┼────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)

    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            line = line.rstrip()
            typer.secho(f"{i:6} │ ", fg=typer.colors.BRIGHT_BLACK, nl=False)

            # Syntax highlighting
            if line.strip().startswith('#'):
                # Comments
                typer.secho(line, fg=typer.colors.BRIGHT_BLACK)
            elif line.strip().startswith('[') and line.strip().endswith(']'):
                # Section headers
                typer.secho(line, fg=typer.colors.BLUE, bold=True)
            elif '=' in line and not line.strip().startswith('#'):
                # Key-value pairs
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0]
                    value = parts[1]
                    typer.secho(key, fg=typer.colors.CYAN, nl=False)
                    typer.secho("=", fg=typer.colors.WHITE, nl=False)

                    # Color values differently
                    if value.strip().startswith('"') and value.strip().endswith('"'):
                        # String values
                        typer.secho(value, fg=typer.colors.GREEN)
                    elif value.strip().lower() in ['true', 'false']:
                        # Boolean values
                        typer.secho(value, fg=typer.colors.YELLOW)
                    else:
                        # Other values
                        typer.secho(value, fg=typer.colors.MAGENTA)
                else:
                    typer.echo(line)
            elif line.strip() == '':
                typer.echo("")
            else:
                typer.echo(line)

        typer.secho(f"───────┴────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)

    except Exception as e:
        typer.secho(f"Error reading environment registry: {e}", fg=typer.colors.RED)


def _show_summary_msg_reset(registry_name: str) -> None:
    """Function to show the summary message of the reset command."""
    typer.echo(f'\n🎉 Environment "{registry_name}" reset successfully!')
    typer.echo(f'📖 Registry updated at: ~/.config/gvit/envs/{registry_name}.toml')
