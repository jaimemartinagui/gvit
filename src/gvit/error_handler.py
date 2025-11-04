"""Global error handler for logging error messages before Exit."""

import typer

_last_error_message = ""


def set_error_message(message: str) -> None:
    """Set the error message to be logged."""
    global _last_error_message
    _last_error_message = message


def get_error_message() -> str:
    """Get the stored error message."""
    return _last_error_message


def clear_error_message() -> None:
    """Clear the error message."""
    global _last_error_message
    _last_error_message = ""


def exit_with_error(message: str, code: int = 1) -> None:
    """Set error message and exit with given code."""
    set_error_message(message)
    raise typer.Exit(code=code)
