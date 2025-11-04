"""
Logging module for gvit command tracking.

Logs command executions to CSV file in ~/.config/gvit/logs/
with rotation and filtering capabilities.
"""

import csv
import os
from datetime import datetime

import typer

from gvit.utils.globals import LOGS_DIR, LOG_FILE, DEFAULT_LOG_MAX_ENTRIES, DEFAULT_LOG_ENABLED
from gvit.utils.utils import load_local_config, save_local_config


class GvitLogger:

    def __init__(self) -> None:
        self.local_config = load_local_config()
        self.ensure_dir()

    def log_command(
        self,
        command_short: str,
        command_full: str,
        environment: str = "",
        exit_code: int = 0,
        duration_ms: int | None = None,
        error: str = "",
    ) -> None:
        """Log a command execution to CSV file."""
        if not self.is_enabled() or self.is_command_ignored(command_short):
            return None

        self.rotate_log_file()

        entry = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            "environment": environment,
            "command_short": command_short,
            "command_full": command_full,
            "exit_code": exit_code,
            "duration_ms": duration_ms if duration_ms is not None else "",
            "error": error,
        }

        file_exists = LOG_FILE.exists()

        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            fieldnames = [
                "timestamp",
                "user",
                "environment",
                "command_short",
                "command_full",
                "exit_code",
                "duration_ms",
                "error",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry)

    def ensure_dir(self) -> None:
        """Create logs directory if it does not exist."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def is_enabled(self) -> bool:
        """Check if logging is enabled in config."""
        logging_config = self.local_config.get("logging", {})
        return logging_config.get("enabled", DEFAULT_LOG_ENABLED)

    def enable(self) -> None:
        """Method to enable logging."""
        if self.local_config.get("logging", {}).get("enabled", False):
            typer.secho("ℹ️  Logging is already enabled", fg=typer.colors.CYAN)
            return None
        self.local_config.setdefault("logging", {})["enabled"] = True
        save_local_config(self.local_config)
        typer.secho("✅ Logging enabled", fg=typer.colors.GREEN)

    def disable(self) -> None:
        """Method to disable logging."""
        if not self.local_config.get("logging", {}).get("enabled", True):
            typer.secho("ℹ️  Logging is already disabled", fg=typer.colors.CYAN)
            return None
        self.local_config.setdefault("logging", {})["enabled"] = False
        save_local_config(self.local_config)
        typer.secho("✅ Logging disabled", fg=typer.colors.GREEN)

    def is_command_ignored(self, command_short: str) -> bool:
        """Check if command should be ignored from logging."""
        logging_config = self.local_config.get("logging", {})
        ignored_commands = logging_config.get("ignored", [])
        return command_short in ignored_commands

    def get_max_log_entries(self) -> int:
        """Get maximum number of log entries from config."""
        logging_config = self.local_config.get("logging", {})
        return logging_config.get("max_entries", DEFAULT_LOG_MAX_ENTRIES)

    def clear_logs(self) -> None:
        """Clear all log entries."""
        typer.echo("- Clearing logs...", nl=False)
        if not LOG_FILE.exists():
            typer.secho("⚠️  No logs to clear", fg=typer.colors.YELLOW)
            return None
        LOG_FILE.unlink()
        typer.echo("✅")

    def get_stats(self) -> dict:
        """Get statistics about logs."""
        if not LOG_FILE.exists():
            return self._get_empty_stats()
        logs = self.read_logs()
        if not logs:
            return self._get_empty_stats()
        return {
            "total_entries": len(logs),
            "file_size_bytes": LOG_FILE.stat().st_size,
            "oldest_entry": logs[-1]["timestamp"],
            "newest_entry": logs[0]["timestamp"],
        }

    def read_logs(self, limit: int | None = None) -> list[dict]:
        """Read log entries from CSV file."""
        if not LOG_FILE.exists():
            return []
        with open(LOG_FILE, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        # Return most recent first
        rows.reverse()
        return rows[:limit] if limit else rows

    def rotate_log_file(self) -> None:
        """Rotate log file if it exceeds max entries. Keeps only the most recent entries."""
        if not LOG_FILE.exists():
            return None
        # Substract 1 to max_entries so that the limit is not exceeded when adding the new entry
        max_entries = self.get_max_log_entries() - 1
        with open(LOG_FILE, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if len(rows) <= max_entries:
            return None
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            if recent_rows := rows[-max_entries:]:
                writer = csv.DictWriter(f, fieldnames=recent_rows[0].keys())
                writer.writeheader()
                writer.writerows(recent_rows)

    def _get_empty_stats(self) -> dict:
        """Method to get stats when log file does not exist or is empty."""
        return {
            "total_entries": 0,
            "file_size_bytes": 0,
            "oldest_entry": None,
            "newest_entry": None,
        }
