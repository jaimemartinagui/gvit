"""
gvit CLI.
"""

import sys

import typer
from click import Group

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.commit import commit
from gvit.commands.status import status
from gvit.commands.init import init
from gvit.commands.setup import setup as setup_repo
from gvit.commands.tree import tree
from gvit.commands.envs import list_, delete, show as show_env, prune, reset, show_activate, show_deactivate
from gvit.commands.config import setup, add_extra_deps, remove_extra_deps, show
from gvit.utils.utils import get_version
from gvit.utils.globals import ASCII_LOGO
from gvit.git import Git


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=False,
    invoke_without_command=True
)

config = typer.Typer(help="Configuration management commands.")
config.command()(setup)
config.command()(add_extra_deps)
config.command()(remove_extra_deps)
config.command()(show)

envs = typer.Typer(help="Environments management commands.")
envs.command(name="list")(list_)
envs.command()(delete)
envs.command()(reset)
envs.command(name="show")(show_env)
envs.command()(prune)
envs.command()(show_activate)
envs.command()(show_deactivate)

app.add_typer(config, name="config")
app.add_typer(envs, name="envs")
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
    """Main CLI entry point with git fallback for unknown commands."""
    # Check if we should try git fallback before Typer processes
    if len(sys.argv) > 1:
        command = sys.argv[1]
        # Get gvit commands dynamically from the app
        click_app = typer.main.get_command(app)
        gvit_commands = set(click_app.commands.keys()) if isinstance(click_app, Group) else set()
        if command not in gvit_commands and not command.startswith("-"):
            git = Git()
            resolved_command = git.resolve_alias(command)
            # If it is a resolved gvit command, use that instead
            if resolved_command in gvit_commands:
                sys.argv[1] = resolved_command
            elif git.command_exists(command):
                git.run(sys.argv[1:])

    # Otherwise, let Typer handle it
    app()


if __name__ == "__main__":
    gvit_cli()
