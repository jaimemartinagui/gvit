"""
gvit CLI.
"""

import sys

import typer

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.commit import commit
from gvit.commands.status import status
from gvit.commands.init import init
from gvit.commands.setup import setup as setup_repo
from gvit.commands.tree import tree
from gvit.commands.envs import list_, delete, show as show_env, prune, reset
from gvit.commands.config import setup, add_extra_deps, remove_extra_deps, show
from gvit.utils.utils import get_version
from gvit.utils.globals import ASCII_LOGO


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

config = typer.Typer(help="Configuration management commands.")
config.command()(setup)
config.command()(add_extra_deps)
config.command()(remove_extra_deps)
config.command()(show)

envs = typer.Typer(help="Environments management commands.")
envs.command(name="list")(list_)
envs.command(name="delete")(delete)
envs.command(name="reset")(reset)
envs.command(name="show")(show_env)
envs.command(name="prune")(prune)

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


if __name__ == "__main__":
    app()
