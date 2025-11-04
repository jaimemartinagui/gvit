"""
gvit CLI.
"""

import os
import sys
import time
from pathlib import Path

import typer

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.commit import commit
from gvit.commands.status import status
from gvit.commands.init import init
from gvit.commands.setup import setup as setup_repo
from gvit.commands.tree import tree
from gvit.commands.envs import list_, delete, show as show_env, prune, reset, show_activate, show_deactivate
from gvit.commands.config import setup, add_extra_deps, remove_extra_deps, show as show_config
from gvit.commands.logs import show as show_logs, clear, stats, enable, disable, config as config_logs
from gvit.utils.utils import get_app_commands, get_version
from gvit.utils.globals import ASCII_LOGO
from gvit.git import Git
from gvit.logger import GvitLogger
from gvit.env_registry import EnvRegistry


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=False,
    invoke_without_command=True
)

config = typer.Typer(help="Configuration management commands.")
config.command()(setup)
config.command()(add_extra_deps)
config.command()(remove_extra_deps)
config.command()(show_config)

envs = typer.Typer(help="Environments management commands.")
envs.command(name="list")(list_)
envs.command()(delete)
envs.command()(reset)
envs.command(name="show")(show_env)
envs.command()(prune)
envs.command()(show_activate)
envs.command()(show_deactivate)

logs = typer.Typer(help="Log management commands.")
logs.command(name="show")(show_logs)
logs.command()(clear)
logs.command()(stats)
logs.command()(enable)
logs.command()(disable)
logs.command(name="config")(config_logs)

app.add_typer(config, name="config")
app.add_typer(envs, name="envs")
app.add_typer(logs, name="logs")
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(clone)
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(commit)
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(init)
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(pull)
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(status)
app.command(name="setup")(setup_repo)
app.command()(tree)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-V", is_flag=True, help="Show the version and exit.")
) -> None:
    """gvit - Git-aware Virtual Environment Manager"""
    if len(sys.argv) == 1:
        typer.echo(ASCII_LOGO)
        typer.echo("Use `gvit --help` to see available commands.\n")
        raise typer.Exit()
    if version:
        typer.echo(get_version())
        raise typer.Exit()


def gvit_cli() -> None:
    """
    Main CLI entry point with git fallback for unknown commands.

    Flow:
    1. Parse command from argv.
    2. Check if it is a git command/alias, delegate if so (do not log).
    3. Execute gvit command via typer.
    4. Log command execution (time, exit code, etc.).
    """
    start_time = time.time()
    exit_code = 0
    error_msg = ""
    command_info = _parse_command_from_argv()

    if command_info and command_info["is_git_fallback"]:
        Git().run(sys.argv[1:])
        return None

    try:
        app()
    except SystemExit as e:
        # Capture exit code and re-raise to maintain normal exit behavior
        exit_code = int(e.code) if e.code is not None else 0
        raise
    except Exception as e:
        # Capture unexpected errors with exit code 1, then re-raise
        exit_code = 1
        # Capture error type and message (without full traceback for brevity)
        error_msg = f"{type(e).__name__}: {str(e)}"
        raise
    finally:
        if command_info and command_info["should_log"]:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_command(
                command=command_info["command"],
                exit_code=exit_code,
                duration_ms=duration_ms,
                error=error_msg,
            )


def _parse_command_from_argv() -> dict | None:
    """
    Parse and resolve command from sys.argv.

    Handles:
    - Git alias resolution.
    - Git command fallback.
    - gvit commands.
    - Help/version flags (no logging).

    Returns:
        None if no command to process or dict with keys:
            - command: str - The command name.
            - is_git_fallback: bool - Whether to delegate to git.
            - should_log: bool - Whether to log this command.
    """
    if len(sys.argv) <= 1:
        return None

    command = sys.argv[1]

    # Do not log help/version flags
    if command in ["-h", "--help", "-V", "--version"] or command.startswith("-"):
        return None

    gvit_commands = get_app_commands(app)

    if command in gvit_commands:
        return {
            "command": command,
            "is_git_fallback": False,
            "should_log": True,
        }

    git = Git()

    if (resolved := git.resolve_alias(command)) in gvit_commands:
          # Replace alias with actual command
        sys.argv[1] = resolved
        return {
            "command": resolved,
            "is_git_fallback": False,
            "should_log": True,
        }

    if git.command_exists(command):
        return {
            "command": command,
            "is_git_fallback": True,
            "should_log": False,
        }


def _log_command(command: str, exit_code: int, duration_ms: int, error: str = "") -> None:
    """Log command execution to the logger."""
    group_commands = ["config", "envs", "logs"]
    no_env_commands = ["config", "envs.list", "envs.prune", "logs", "tree"]

    if len(sys.argv) > 2 and command in group_commands:
        subcommand = sys.argv[2]
        command_short = f"{command}.{subcommand}" if not subcommand.startswith("-") else command
    else:
        command_short = command

    command_full = f'gvit {" ".join(sys.argv[1:])}'
    environment = "" if command_short in no_env_commands else _detect_environment_from_argv()

    logger = GvitLogger()
    logger.log_command(
        command_short=command_short,
        command_full=command_full,
        environment=environment,
        exit_code=exit_code,
        duration_ms=duration_ms,
        error=error,
    )


def _detect_environment_from_argv() -> str:
    """
    Detect environment name from command arguments.

    Priority:
    1. --venv-name or -n flag (explicit environment name).
    2. Positional argument for commands like "envs delete <name>", "envs show <name>".
    3. --target-dir or -t flag (lookup in registry by repo path).
    4. Current working directory (lookup in registry by repo path).

    Returns:
        Environment name or empty string if not found
    """
    # Try to find --venv-name or -n flag
    for i, arg in enumerate(sys.argv):
        if arg in ["--venv-name", "-n"] and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    
    # For commands like "envs delete <name>" or "envs show <name>", check positional arg
    if len(sys.argv) >= 3:
        command = sys.argv[1]
        subcommand = sys.argv[2]
        
        # Commands that take env name as positional argument
        env_commands = ["delete", "show", "reset", "show-activate", "show-deactivate"]
        
        if command == "envs" and subcommand in env_commands and len(sys.argv) >= 4:
            # Third argument is the env name (e.g., "gvit envs delete my-env")
            potential_env = sys.argv[3]
            if not potential_env.startswith("-"):
                return potential_env
    
    # Try to find --target-dir or -t flag
    target_dir = None
    for i, arg in enumerate(sys.argv):
        if arg in ["--target-dir", "-t"] and i + 1 < len(sys.argv):
            target_dir = Path(sys.argv[i + 1]).resolve()
            break
    
    # If no target-dir, use current working directory
    if not target_dir:
        target_dir = Path(os.getcwd()).resolve()
    
    # Lookup in registry by repository path
    registry = EnvRegistry()
    for env in registry.get_environments():
        repo_path = Path(env["repository"]["path"]).resolve()
        if repo_path == target_dir:
            return env["environment"]["name"]
    
    return ""


if __name__ == "__main__":
    gvit_cli()
