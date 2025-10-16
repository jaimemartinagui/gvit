"""
gvit CLI.
"""

import typer

from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.config import config


app = typer.Typer(help="gvit - Git-aware Virtual Environment manager")

app.command()(config)
app.command()(pull)
app.command()(clone)


if __name__ == "__main__":
    app()
