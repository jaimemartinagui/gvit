"""
Module for the "gvit envs" group of commands.
"""

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.globals import ENVS_DIR
from gvit.backends.conda import CondaBackend


def list_() -> None:
    """List the environments tracked in the gvit environment registry."""
    env_registry = EnvRegistry()
    envs = env_registry.list_environments()
    if not envs:
        typer.echo("No environments in registry.")
        return None

    typer.echo("Tracked environments:")
    for env_name in envs:
        if env_info := env_registry.load_environment_info(env_name):
            backend = env_info['environment']['backend']
            python = env_info['environment']['python']
            repo_path = env_info['repository']['path']

            if backend == "conda":
                conda_backend = CondaBackend()
                activate_cmd = conda_backend.get_activate_cmd(env_name)
            else:
                activate_cmd = f"# Activate command for {backend} not available"

            typer.secho(f"\n  • {env_name}", fg=typer.colors.CYAN, bold=True)
            typer.echo(f"    Backend:    {backend}")
            typer.echo(f"    Python:     {python}")
            typer.echo(f"    Location:   {repo_path}")
            typer.secho(f"    Command:    ", nl=False, dim=True)
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
    env_info = env_registry.load_environment_info(venv_name)
    if env_info is None:
        typer.secho(f'⚠️  Environment "{venv_name}" not found.', fg=typer.colors.YELLOW)
        return None

    typer.echo(f'- Removing environment "{venv_name}" backend...', nl=False)
    if env_info["environment"]["backend"] == "conda":
        conda_backend = CondaBackend()
        conda_backend.delete_environment(venv_name, verbose)
    typer.echo("✅")

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
    for env_info in orphaned_envs:
        typer.echo(f"  • {env_info['environment']['name']} ({env_info['environment']['backend']}) -> {env_info['repository']['path']}")

    if dry_run:
        typer.echo("\n[DRY RUN] No changes made. Run without --dry-run to actually prune.")
        return None

    if not yes and not typer.confirm("\n  Do you want to delete these environments?", default=False):
        typer.secho("  Aborted!", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    errors_registry = []
    errors_backend = []
    for env_info in orphaned_envs:
        env_name = env_info["environment"]["name"]
        typer.echo(f'\n- Pruning "{env_name}" environment:')

        typer.echo("  Deleting backend...", nl=False)
        try:
            if env_info["environment"]["backend"] == "conda":
                conda_backend = CondaBackend()
                if conda_backend.environment_exists(env_name):
                    conda_backend.delete_environment(env_name, verbose=verbose)
                    typer.echo("✅")
                else:
                    typer.secho('⚠️  Environment not found in backend', fg=typer.colors.YELLOW)
        except Exception:
            errors_backend.append(env_name)
            continue

        typer.echo("  Deleting registry...", nl=False)
        if env_registry.delete_environment_registry(env_name):
            typer.echo("✅")
        else:
            errors_registry.append(env_name)
            typer.secho("❗ Failed to delete registry", fg=typer.colors.RED)

    pruned_envs = [
        env_info["environment"]["name"]
        for env_info in orphaned_envs
        if env_info["environment"]["name"] not in errors_registry + errors_backend
    ]
    if pruned_envs:
        typer.echo(f"\n🎉 Pruned {len(pruned_envs)} environment(s).")
    if errors_registry:
        typer.secho(f'\n⚠️  Errors on registry deletion: {errors_registry}', fg=typer.colors.YELLOW)
    if errors_backend:
        typer.secho(f'\n⚠️  Errors on backend deletion: {errors_backend}', fg=typer.colors.YELLOW)


def show(venv_name: str = typer.Argument(help="Name of the environment to display.")) -> None:
    """Display the environment registry file for a specific environment."""
    env_registry = EnvRegistry()

    if not env_registry.environment_exists_in_registry(venv_name):
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
