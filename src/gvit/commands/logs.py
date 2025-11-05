"""
Logs management commands for gvit.

Provides commands to view, clear and manage command execution logs.
"""

import typer
from rich.console import Console
from rich.table import Table

from gvit.logger import GvitLogger
from gvit.utils.globals import LOG_FILE, DEFAULT_LOG_ENABLED, DEFAULT_LOG_SHOW_LIMIT
from gvit.utils.utils import load_local_config, save_local_config


console = Console()


def enable() -> None:
    """Enable logging.""" 
    gvit_logger = GvitLogger()
    gvit_logger.enable()


def disable() -> None:
    """Disable logging."""    
    gvit_logger = GvitLogger()
    gvit_logger.disable()


def clear(yes: bool = typer.Option(False, "--yes", "-y", is_flag=True, help="Skip confirmation.")) -> None:
    """Clear all command logs."""
    if not yes:
        if not typer.confirm(
            typer.style("Are you sure you want to clear all logs?", fg=typer.colors.RED),
            default=False,
        ):
            typer.secho("Aborted!", fg=typer.colors.RED)
            return None
        typer.echo()
    gvit_logger = GvitLogger()
    gvit_logger.clear_logs()


def stats() -> None:
    """Show logs statistics."""
    gvit_logger = GvitLogger()
    stats = gvit_logger.get_stats()
    file_bytes = stats['file_size_bytes']
    console.print("[bold]📂 Logs Statistics[/bold]\n")
    console.print(f"- [green]Total entries:[/green] {stats['total_entries']}")
    console.print(f"- [green]File size:[/green] {file_bytes} bytes ({round(file_bytes / 1_000_000, 2)} MB)")
    console.print(f"- [dim]Newest entry:[/dim] {stats['newest_entry']}")
    console.print(f"- [dim]Oldest entry:[/dim] {stats['oldest_entry']}")


def config(
    max_entries: int = typer.Option(None, "--max-entries", "-e", help="Maximum number of log entries to keep."),
    ignore: str = typer.Option(None, "--ignore", "-i", help="Commands to ignore (comma-separated)."),
    show: bool = typer.Option(False, "--show", "-s", is_flag=True, help="Show current configuration."),
) -> None:
    """Configure logging settings."""    
    config = load_local_config()
    logging = config.get("logging", {})
    if show:
        if not logging:
            console.print("[yellow]No logging configuration found.[/yellow]")
            return None

        console.print("[cyan bold]🔧 Logging Configuration[/cyan bold]\n")

        enabled = logging.get("enabled", DEFAULT_LOG_ENABLED)
        max_entries = logging.get("max_entries", 1000)
        ignored = logging.get("ignored", [])

        enabled_str = "[green]✅ Enabled[/green]" if enabled else "[red]❌ Disabled[/red]"

        console.print(f"- Status: {enabled_str}")
        console.print(f"- Max entries: {max_entries}")
        console.print(f"- [dim]Ignored commands: {', '.join(ignored) if ignored else 'None'}[/dim]")
        return None

    if "logging" not in config:
        config["logging"] = {}

    if max_entries is not None:
        config["logging"]["max_entries"] = max_entries

    if ignore is not None:
        config["logging"]["ignored"] = [cmd.strip() for cmd in ignore.split(",") if cmd.strip()]

    typer.echo("- Saving logging configuration...", nl=False)
    save_local_config(config)
    typer.echo("✅")


def show(
    limit: int = typer.Option(DEFAULT_LOG_SHOW_LIMIT, "--limit", "-l", help="Number of entries to show."),
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Filter logs by environment name."),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter logs by status (exit code). Comma separated values."),
    errors: bool = typer.Option(False, "--errors", "-e", is_flag=True, help="Show error messages."),
    full_command: bool = typer.Option(False, "--full-command", "-f", is_flag=True, help="Show full command."),
) -> None:
    """
    Show recent command logs.

    Use --venv-name to filter by environment.
    """
    gvit_logger = GvitLogger()
    stats = gvit_logger.get_stats()
    total_entries = stats["total_entries"]

    if total_entries == 0:
        console.print("[yellow]No logs found.[/yellow]")
        return None

    console.print(f"[cyan]📂 Logs Directory:[/cyan] {LOG_FILE.parent}")
    console.print(f"   [dim]{total_entries} entries | {stats['newest_entry']} - {stats['oldest_entry']}[/dim]\n")

    logs = gvit_logger.read_logs()
    if not logs:
        console.print("[yellow]No logs found.[/yellow]")
        return None

    if venv_name:
        logs = [log for log in logs if log["environment"] == venv_name]
        if not logs:
            console.print(f"[yellow]⚠️  No logs found for environment: {venv_name}[/yellow]")
            return None

    if status:
        logs = [log for log in logs if log["exit_code"] in status.split(",")]
        if not logs:
            console.print(f"[yellow]⚠️  No logs found for status: {status}[/yellow]")
            return None

    n_entries_after_filter = len(logs)

    logs = logs[:limit] if limit else logs

    table = Table(show_header=True, header_style="bold cyan", show_lines=True)
    table.add_column("n", style="green")
    table.add_column("Timestamp", style="green")
    table.add_column("Command", style="cyan")
    table.add_column("Environment", style="yellow")
    table.add_column("Duration", style="magenta", justify="right")
    table.add_column("Status", justify="center")
    if full_command:
        table.add_column("Full Command", style="dim")
    if errors:
        table.add_column("Error", style="red")

    for i, entry in enumerate(logs):
        duration = f"{entry['duration_ms']}ms" if entry['duration_ms'] else "-"
        status_ = "✅" if entry['exit_code'] == "0" else f"{entry['exit_code']} ❌"
        env = entry.get("environment", "") or "-"
        error = entry.get("error", "") or "-"
        row_data = [
            str(i + 1),
            entry["timestamp"],
            entry["command_short"],
            env,
            duration,
            status_,
        ]
        if full_command:
            row_data.append(entry["command_full"])
        if errors:
            row_data.append(error)
        table.add_row(*row_data)

    console.print(table)

    if len(logs) < n_entries_after_filter:
        typer.secho(f" Showing {len(logs)} entries out of {n_entries_after_filter}.", dim=True)
