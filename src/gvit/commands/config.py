"""
Module for the "gvit config" group of commands.
"""

import time

from typing import cast

import typer

from gvit.utils.globals import SUPPORTED_BACKENDS, FAKE_SLEEP_TIME, LOCAL_CONFIG_FILE
from gvit.utils.utils import (
    ensure_local_config_dir,
    load_local_config,
    save_local_config,
    get_backend,
    get_venv_name,
    get_python,
    get_base_deps
)
from gvit.utils.validators import validate_backend, validate_python
from gvit.utils.schemas import LocalConfig
from gvit.utils.exceptions import CondaNotFoundError
from gvit.backends.conda import CondaBackend


def setup(
    backend: str = typer.Option(None, "--backend", "-b", help=f"Default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})."),
    python: str = typer.Option(None, "--python", "-p", help="Default Python version."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Default base dependencies path (relative to repository root path)."),
) -> None:
    """
    Configure gvit and generate ~/.config/gvit/config.toml configuration file.

    It defines the DEFAULT options to be used if not provided in the different commands or in the repository config.

    Omitted options will be requested via interactive prompts.
    """
    ensure_local_config_dir()
    config = load_local_config()

    if backend is None:
        backend = typer.prompt(
            f"- Select default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})",
            default=get_backend(config),
        ).strip()
    validate_backend(backend)
    conda_path = None
    venv_name = None
    if backend == "conda":
        conda_backend = CondaBackend()
        conda_path = conda_backend.path
        if not conda_backend.is_available():
            raise CondaNotFoundError(
                "Conda is not installed or could not be found in common installation paths. "
                "You can also specify the path manually in your configuration file under "
                "`backends.conda.path`."
            )
    elif backend in ["venv", "virtualenv"]:
        venv_name = typer.prompt(
            f"- Select default virtual environment name",
            default=get_venv_name(config),
        ).strip()

    if python is None:
        python = typer.prompt(
            f"- Select default Python version",
            default=get_python(config),
        ).strip()
    validate_python(python)

    if base_deps is None:
        base_deps = typer.prompt(
            f"- Select default dependencies path",
            default=get_base_deps(config),
        ).strip()

    config = _get_updated_local_config(backend, python, base_deps, conda_path, venv_name)

    typer.echo("\nSaving configuration...", nl=False)
    save_local_config(config)
    time.sleep(FAKE_SLEEP_TIME)
    typer.echo("✅")


def add_extra_deps(
    key: str = typer.Argument(help="The dependency group name (e.g., 'dev', 'internal')."),
    value: str = typer.Argument(help="The path to the dependency file (e.g., 'requirements-dev.txt')."),
) -> None:
    """
    Add an extra dependency group to the local configuration.

    This adds a new entry to the [deps] section in ~/.config/gvit/config.toml.

    Example: `gvit config add-extra-deps dev requirements-dev.txt`
    """
    ensure_local_config_dir()
    config_data = load_local_config()
    if "deps" not in config_data:
        config_data["deps"] = {}
    config_data["deps"][key] = value
    typer.secho(f"Adding extra dependency ({key} = {value})...", nl=False, fg=typer.colors.GREEN)
    save_local_config(config_data)
    time.sleep(FAKE_SLEEP_TIME)
    typer.echo("✅")


def remove_extra_deps(
    key: str = typer.Argument(help="The dependency group name to remove (e.g., 'dev', 'test')."),
) -> None:
    """
    Remove an extra dependency group from the local configuration.

    This removes an entry from the [deps] section in ~/.config/gvit/config.toml.

    Example: `gvit config remove-extra-deps dev`
    """
    ensure_local_config_dir()
    config_data = load_local_config()

    if not config_data:
        typer.secho(f"No configuration file was found.", fg=typer.colors.YELLOW)
        typer.echo("\nRun `gvit config setup` to create initial configuration.")
        return None

    if "deps" not in config_data:
        typer.secho(f"No deps section in configuration file.", fg=typer.colors.YELLOW)
        return None

    if key not in config_data["deps"]:
        typer.secho(f'Dependency group "{key}" not found.', fg=typer.colors.YELLOW)
        available_keys = [k for k in config_data["deps"].keys() if k != "_base"]
        if available_keys:
            typer.echo(f"\nAvailable dependency groups: {available_keys}.")
        return None

    if key == "_base":
        typer.secho("Cannot remove '_base' - reserved dependency setting.", fg=typer.colors.RED)
        return None

    removed_value = config_data["deps"].pop(key)
    typer.secho(f"Removing extra dependency ({key} = {removed_value})...", nl=False, fg=typer.colors.GREEN)
    save_local_config(config_data)
    time.sleep(FAKE_SLEEP_TIME)
    typer.echo("✅")


def show() -> None:
    """Display the current gvit configuration file."""
    if not LOCAL_CONFIG_FILE.exists():
        typer.secho(f"Configuration file not found: {LOCAL_CONFIG_FILE}", fg=typer.colors.YELLOW)
        typer.echo("\nRun `gvit config setup` to create initial configuration.")
        return None

    typer.secho(f"───────┬────────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)
    typer.secho(f"       │ File: {LOCAL_CONFIG_FILE}", fg=typer.colors.BRIGHT_BLACK)
    typer.secho(f"───────┼────────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)

    try:
        with open(LOCAL_CONFIG_FILE, 'r') as f:
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

        typer.secho(f"───────┴────────────────────────────────────────────────────────────", fg=typer.colors.BRIGHT_BLACK)

    except Exception as e:
        typer.secho(f"Error reading configuration: {e}", fg=typer.colors.RED)


def _get_updated_local_config(
    backend: str, python: str, base_deps: str, conda_path: str | None, venv_name: str | None
) -> LocalConfig:
    """Build the local configuration file, preserving existing extra deps."""
    existing_config = load_local_config()
    config = {
        "gvit": {
            "backend": backend,
            "python": python,
        },
        "deps": {
            "_base": base_deps,
            # Preserve existing extra deps (dev, test, etc.)
            **{k: v for k, v in existing_config.get("deps", {}).items() if k != "_base"}
        }
    }
    if conda_path or venv_name:
        config["backends"] = existing_config.get("backends", {})
        if conda_path:
            config["backends"]["conda"] = {"path": conda_path}
        if venv_name:
            config["backends"]["venv"] = {"name": venv_name}

    return cast(LocalConfig, config)
