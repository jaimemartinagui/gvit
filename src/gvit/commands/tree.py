"""
Module for the "gvit tree" command.
"""

import typer
from click import Group


def tree(ctx: typer.Context) -> None:
    """Display all available commands in a tree structure."""
    typer.echo("gvit")
    # Get the root Click group from context
    root = ctx.find_root().command
    # Type check to satisfy Pylance
    if not isinstance(root, Group):
        return None
    commands = sorted(root.commands.items())
    for i, (name, cmd) in enumerate(commands):
        is_last = i == len(commands) - 1
        prefix = "└──" if is_last else "├──"
        if not isinstance(cmd, Group):
            typer.echo(f"{prefix} {name}")
            continue
        typer.secho(f"{prefix} {name}", fg=typer.colors.CYAN, bold=True)
        subcommands = sorted(cmd.commands.items())
        for j, (sub_name, _) in enumerate(subcommands):
            is_last_sub = j == len(subcommands) - 1
            continuation = "    " if is_last else "│   "
            sub_prefix = "└──" if is_last_sub else "├──"
            typer.echo(f"{continuation}{sub_prefix} {sub_name}")
