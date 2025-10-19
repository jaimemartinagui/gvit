"""
Module for the options of the "gvit clone" command.
"""

from typer import Option

from gvit.utils.globals import SUPPORTED_BACKENDS


target_dir_option = Option(None, "--target-dir", "-t", help="Directory to clone into.")

backend_option = Option(
    None, "--backend", "-b", help=f"Virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)}).",
)

python_option = Option(None, "--python", "-p", help="Python version.")

install_deps_option = Option(None, "--install-deps", "-i", help="Install dependencies in the virtual environment.")

deps_path_option = Option(None, "--deps-path", "-d", help="Path where to look for the dependencies (relative to repository root path).")

verbose_option = Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
