"""
gvit CLI.
"""

import sys

import typer

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.config import config
from gvit.options.cli import version_option
from gvit.utils.utils import get_version
from gvit.utils.globals import ASCII_LOGO


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

app.command()(config)
app.command()(pull)
app.command()(clone)


@app.callback(invoke_without_command=True)
def main(version: bool = version_option) -> None:
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
