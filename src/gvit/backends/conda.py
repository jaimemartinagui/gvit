"""
Module with the Conda backend class.
"""

from pathlib import Path
import shutil
import platform
import os
import subprocess
import json

import typer


class CondaBackend:
    """Class for the operations with the Conda backend."""

    def get_path(self) -> str | None:
        """Try to find the conda executable in PATH or common install locations."""
        if conda_path := shutil.which("conda"):
            return conda_path

        home = Path.home()
        candidates = []

        if platform.system() == "Windows":
            common_dirs = [
                home / "Anaconda3",
                home / "Miniconda3",
                home / "Miniforge3",
                Path("C:/ProgramData/Anaconda3"),
                Path("C:/ProgramData/Miniconda3"),
                Path("C:/ProgramData/Miniforge3"),
            ]
            for d in common_dirs:
                candidates.append(d / "Scripts" / "conda.exe")

        else:  # Linux / macOS
            common_dirs = [
                home / "anaconda3",
                home / "miniconda3",
                home / "miniforge3",
                Path("/opt/anaconda3"),
                Path("/opt/miniconda3"),
                Path("/opt/miniforge3"),
                home / ".conda",
            ]
            for d in common_dirs:
                candidates.append(d / "bin" / "conda")

            # Check if there is a conda.sh for initialization
            for d in common_dirs:
                conda_sh = d / "etc" / "profile.d" / "conda.sh"
                if conda_sh.exists():
                    # Try to derive the executable from the parent directory
                    possible = d / "bin" / "conda"
                    candidates.append(possible)

        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)

        return None

    def is_available(self, conda_path: str) -> bool:
        """Check if Conda is functional by running `conda info --json`."""
        try:
            result = subprocess.run(
                [conda_path, "info", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            return "conda_version" in json.loads(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return False

    def create_venv(self, venv_name: str, python: str, verbose: bool) -> None:
        """Function to create the virtual environment using conda."""
        try:
            result = subprocess.run(
                ["conda", "create", "--name", venv_name, f"python={python}", "--yes"],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to create conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def install_deps(self, venv_name: str, deps_path: str, verbose: bool) -> None:
        """Function to install the dependencies in the conda environment."""
        if "requirements.txt" in deps_path:
            deps_install_command = ["pip", "install", "-r", deps_path]
        elif "pyproject.toml" in deps_path:
            deps_install_command = ["pip", "install", "-e", deps_path]
        else:
            raise Exception("Only requirements.txt and pyporject.toml are supported!")

        try:
            result = subprocess.run(
                ["conda", "run", "-n", venv_name] + deps_install_command,
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to install dependencies to conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def show_activate_message(self, venv_name: str) -> None:
        """Function to show the command to activate the environment."""
        typer.secho(f"conda activate {venv_name}", fg=typer.colors.YELLOW)
