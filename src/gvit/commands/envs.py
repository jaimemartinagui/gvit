"""
Module for the "gvit envs" group of commands.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

import toml
import typer
import questionary
import pyperclip

from gvit.env_registry import EnvRegistry
from gvit.utils.globals import ENVS_DIR, DEFAULT_LOG_SHOW_LIMIT
from gvit.utils.utils import load_local_config, load_repo_config
from gvit.backends.common import create_venv, delete_venv, install_dependencies, get_activate_cmd, get_deactivate_cmd
from gvit.utils.validators import validate_directory
from gvit.error_handler import exit_with_error
from gvit.commands.logs import show as show_logs


def manage() -> None:
    """
    Interactive environment management.
    
    Select an environment and perform actions on it:
    - Show details
    - Open repository (VSCode, editor, terminal)
    - Reset environment
    - Delete environment
    """    
    env_registry = EnvRegistry()
    envs = env_registry.get_environments()

    if not envs:
        typer.secho("⚠️  No environments in registry.", fg=typer.colors.YELLOW)
        return None

    custom_style = questionary.Style([
        ("qmark", "fg:#00ffaa bold"),
        ("question", "bold"),
        ("answer", "fg:#ffcc00 bold"),
        ("pointer", "fg:#00ffaa bold"),
    ])

    env_choices = [
        f"{env['environment']['name']:30} [{env['environment']['backend']}] - {env['repository']['path']}"
        for env in envs
    ]

    selected = questionary.select(
        "Select environment:",
        choices=env_choices + ["❌ Exit"],
        style=custom_style
    ).ask()

    if selected == "❌ Exit" or selected is None:
        return None

    env = [env for env in envs if env["environment"]["name"] == selected.split()[0]][0]
    venv_name = env["environment"]["name"]
    repo_path = Path(env["repository"]["path"])
    backend = env["environment"]["backend"]
    venv_path = env["environment"]["path"]

    actions = {
        "show": "📊 Show details",
        "logs": "📂 Check logs",
        "reveal": "🔍 Reveal",
        "open_editor": "✏️  Open in default editor",
        "copy": "📎 Copy navigate and activate command",
        "reset": "🔄 Reset environment",
        "delete": "❗ Delete environment",
        "exit": "❌ Exit"
    }

    action = questionary.select(
        f'What do you want to do with "{venv_name}"?',
        choices=list(actions.values()),
        style=custom_style
    ).ask()

    if action is None or action == actions["exit"]:
        return None

    if action == actions["show"]:
        typer.echo()
        show(venv_name)
    if action == actions["logs"]:
        typer.echo()
        show_logs(
            limit=DEFAULT_LOG_SHOW_LIMIT,
            venv_name=venv_name,
            status=None,
            errors=True,
            full_command=True
        )
    elif action == actions["reveal"]:
        _reveal(repo_path)
    elif action == actions["open_editor"]:
        _open_editor(repo_path)
    elif action == actions["copy"]:
        activate_cmd = get_activate_cmd(backend, venv_name, Path(venv_path)) or ""
        pyperclip.copy(f"cd {repo_path} && {activate_cmd}")    
    elif action == actions["reset"]:
        if not typer.confirm(f'  Do you want to reset environment "{venv_name}"?', default=False):
            error_msg = "  Aborted!"
            typer.secho(error_msg, fg=typer.colors.RED)
            exit_with_error(error_msg)
        typer.echo()
        reset(venv_name, no_deps=False, yes=True, verbose=False)
    elif action == actions["delete"]:
        if not typer.confirm(f'  Do you want to delete environment "{venv_name}"?', default=False):
            error_msg = "  Aborted!"
            typer.secho(error_msg, fg=typer.colors.RED)
            exit_with_error(error_msg)
        typer.echo()
        delete(venv_name, verbose=False)


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
        activate_cmd = get_activate_cmd(backend, venv_name, Path(venv_path)) or f"# Activate command for {backend} not available"
        typer.secho(f"\n  • {venv_name}", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"    Backend:       {backend}")
        typer.echo(f"    Python:        {python}")
        typer.echo(f"    Environment:   {venv_path}")
        typer.echo(f"    Repository:    {repo_path}")
        typer.echo(f"    Registry:      {env_registry_file}")
        typer.secho(f"    Command:       ", nl=False, dim=True)
        typer.secho(f"cd {repo_path} && {activate_cmd}", fg=typer.colors.YELLOW)


def show_activate(
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment."),
    relative: bool = typer.Option(False, "--relative", "-r", is_flag=True, help="Show the environment path as relative.")
) -> None:
    """
    Show the activate command for an environment.

    If no environment is provided with the -n option, it looks in the registry for an existing
    environment in the current directory.

    Use the following command to directly activate the environment -> eval "$(gvit envs show-activate)"
    """
    env_registry = EnvRegistry()
    if venv_name:
        env = env_registry.load_environment_info(venv_name)
        if env is None:
            typer.secho(f'⚠️  Environment "{venv_name}" not found.', fg=typer.colors.YELLOW)
            return None
    else:
        cwd = Path(".").resolve()
        envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == cwd]
        if not envs:
            typer.secho("⚠️  No tracked environment found for this repository.", fg=typer.colors.YELLOW)
            return None
        env = envs[0]

    backend = env["environment"]["backend"]
    venv_path = env["environment"]["path"]
    venv_name = env["environment"]["name"]

    activate_cmd = (
        get_activate_cmd(backend, venv_name, Path(venv_path), relative)
        or f"# Activate command for {backend} not available"
    )

    typer.secho(activate_cmd, fg=typer.colors.YELLOW)


def show_deactivate(
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment.")
) -> None:
    """
    Show the deactivate command for an environment.

    If no environment is provided with the -n option, it looks in the registry for an existing
    environment in the current directory.
    
    Use the following command to directly deactivate the environment -> eval "$(gvit envs show-deactivate)"
    """
    env_registry = EnvRegistry()
    if venv_name:
        env = env_registry.load_environment_info(venv_name)
        if env is None:
            typer.secho(f'⚠️  Environment "{venv_name}" not found.', fg=typer.colors.YELLOW)
            return None
    else:
        cwd = Path(".").resolve()
        envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == cwd]
        if not envs:
            typer.secho("⚠️  No tracked environment found for this repository.", fg=typer.colors.YELLOW)
            return None
        env = envs[0]

    backend = env["environment"]["backend"]

    deactivate_cmd = get_deactivate_cmd(backend) or f"# Deactivate command for {backend} not available"

    typer.secho(deactivate_cmd, fg=typer.colors.YELLOW)


def delete(
    venv_name: str = typer.Argument(help="Name of the environment to delete (backend and registry)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Remove the environment without confirmation."),
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

    if not yes and not typer.confirm(f'  Do you want to delete environment "{venv_name}"?', default=False):
        error_msg = "  Aborted!"
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)

    if not yes:
        typer.echo()

    delete_venv(
        backend=venv_info["environment"]["backend"],
        venv_name=venv_name,
        venv_path=venv_info["environment"]["path"],
        repo_path=Path(venv_info["repository"]["path"]),
        verbose=verbose
    )

    typer.echo(f'\n- Deleting environment "{venv_name}" registry...', nl=False)
    if env_registry.delete_environment_registry(venv_name):
        typer.echo("✅")
    else:
        error_msg = f"❗ Registry deletion failed."
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)


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
        error_msg = "  Aborted!"
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)

    errors_registry = []
    errors_backend = []
    for venv_info in orphaned_envs:
        typer.echo()
        venv_name = venv_info["environment"]["name"]

        try:
            delete_venv(
                backend=venv_info["environment"]["backend"],
                venv_name=venv_name,
                venv_path=venv_info["environment"]["path"],
                repo_path=Path(venv_info["repository"]["path"]),
                verbose=verbose
            )
        except Exception:
            errors_backend.append(venv_name)
            continue

        typer.echo(f'\n- Deleting "{venv_name}" registry...', nl=False)
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
        typer.echo()

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


def _reveal(path: Path) -> None:
    """Open a path in the system's file explorer."""
    validate_directory(path)
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", path])
            typer.secho("  ✅ Revealed!", fg=typer.colors.GREEN)
        elif sys.platform == "win32":  # Windows
            os.startfile(path)
            typer.secho("  ✅ Revealed!", fg=typer.colors.GREEN)
        elif sys.platform.startswith("linux"):  # Linux
            subprocess.run(["xdg-open", path])
            typer.secho("  ✅ Revealed!", fg=typer.colors.GREEN)
        else:
            error_msg = "  ⚠️  Unsupported Operating System!"
            typer.secho(error_msg, fg=typer.colors.RED)
            exit_with_error(error_msg)
    except Exception as e:
        error_msg = f"  ❗ Failed to open: {e}"
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)


def _open_editor(path: Path) -> None:
    """Open a path in the default editor."""
    validate_directory(path)
    try:
        code_cmd = shutil.which("code")
        if code_cmd:
            subprocess.run([code_cmd, str(path)])
        else:
            typer.launch(str(path))
        typer.secho("  ✅ Opened!", fg=typer.colors.GREEN)
    except Exception as e:
        error_msg = f"  ❗ Failed to open: {e}"
        typer.secho(error_msg, fg=typer.colors.RED)
        exit_with_error(error_msg)


def _show_summary_msg_reset(registry_name: str) -> None:
    """Function to show the summary message of the reset command."""
    typer.echo(f'\n🎉 Environment "{registry_name}" reset successfully!')
    typer.echo(f'📖 Registry updated at: ~/.config/gvit/envs/{registry_name}.toml')
