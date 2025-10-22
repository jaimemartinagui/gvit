"""
Module for the "gvit envs" group of commands.
"""

import typer

from gvit.env_registry import EnvRegistry


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
