"""
Module for the options of the "gvit config" command.
"""

from typer import Option
from gvit.utils.globals import SUPPORTED_BACKENDS


backend_option = Option(
    None, "--backend", "-b", help=f"Default virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)}).",
)

python_option = Option(None, "--python", "-p", help="Default Python version.")

install_deps_option = Option(None, "--install-deps", "-i", help="Default install-deps in the virtual environment.")

deps_path_option = Option(None, "--deps-path", "-d", help="Default dependencies path (relative to repository root path).")
