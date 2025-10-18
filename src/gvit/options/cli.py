"""
Module with the options for the main callback.
"""

from typer import Option


version_option = Option(False, "--version", "-V", is_flag=True, help="Show the version and exit.")
