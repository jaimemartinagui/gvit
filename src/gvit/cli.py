"""
gvit CLI.
"""

import typer

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.config import config
from gvit.utils.utils import get_version


app = typer.Typer(
    help="gvit - Git-aware Virtual Environment manager",
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.command()(config)
app.command()(pull)
app.command()(clone)

version_option = typer.Option(False, "--version", "-v", is_flag=True, help="Show the version and exit.")

@app.callback(invoke_without_command=True)
def main(version: bool = version_option) -> None:
    """
    Main callback function. It is very similar to @app.command(), but it declares the CLI
    parameters for the main CLI application (before the commands).
    """
    if version:
        typer.echo(get_version())
        raise typer.Exit()


if __name__ == "__main__":
    app()
