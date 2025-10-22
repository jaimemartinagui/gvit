"""
Module for the "gvit envs" group of commands.
"""

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.globals import ENVS_DIR


def list_() -> None:
    """List the environments tracked in the gvit environment registry."""
    envs_registry = EnvRegistry()
    envs = envs_registry.list_environments()
    if not envs:
        typer.echo("No environments in registry.")
    for env_name in envs:
        if env_info := envs_registry.load_environment_info(env_name):
            typer.echo(f"{env_name} -> {env_info['repository']['path']}")


def delete(venv_name: str = typer.Argument(help="Name of the environment to delete from the registry.")) -> None:
    """Remove an environment from the registry."""
    typer.echo(f'- Removing environment "{venv_name}" from registry...', nl=False)
    envs_registry = EnvRegistry()
    if not envs_registry.environment_exists_in_registry(venv_name):
        typer.secho(f'⚠️  Environment "{venv_name}" not found.', fg=typer.colors.YELLOW)
        return None
    if envs_registry.delete_environment_from_registry(venv_name):
        typer.echo("✅")
        return None
    typer.secho(f'❗ Deletion failed.', fg=typer.colors.RED)


def show(venv_name: str = typer.Argument(help="Name of the environment to display.")) -> None:
    """Display the environment registry file for a specific environment."""
    envs_registry = EnvRegistry()

    if not envs_registry.environment_exists_in_registry(venv_name):
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
