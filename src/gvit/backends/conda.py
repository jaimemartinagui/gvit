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

    def __init__(self) -> None:
        self.path = self._get_path() or "conda"

    def get_unique_environment_name(self, venv_name: str) -> str:
        """
        Generate a unique environment name by adding numeric suffix if
        needed (venv_name, venv_name-1, venv_name-2, etc.).
        """
        if not self.environment_exists(venv_name):
            return venv_name
        counter = 1
        while self.environment_exists(f"{venv_name}-{counter}"):
            counter += 1
        return f"{venv_name}-{counter}"

    def is_available(self) -> bool:
        """Check if Conda is functional by running `conda info --json`."""
        try:
            result = subprocess.run(
                [self.path, "info", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            return "conda_version" in json.loads(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return False

    def create_venv(self, venv_name: str, python: str, force: bool, verbose: bool) -> str:
        """
        Function to create the virtual environment using conda.
        It handles the case where an environment witht the same name already exists.
        """
        if self.environment_exists(venv_name):
            if force:
                typer.secho(f"⚠️  Environment '{venv_name}' already exists. Removing it...", fg=typer.colors.YELLOW)
                self.remove_environment(venv_name, verbose)
            typer.secho(f"\n  ⚠️  Environment '{venv_name}' already exists. What would you like to do?", fg=typer.colors.YELLOW)
            choice = typer.prompt(
                "    [1] Use a different name (auto-generate)\n"
                "    [2] Overwrite existing environment\n"
                "    [3] Abort\n"
                "  Select option",
                type=int,
                default=1
            )
            match choice:
                case 1:
                    venv_name = self.get_unique_environment_name(venv_name)
                    typer.echo(f'  Using environment name "{venv_name}"...', nl=False)
                case 2:
                    typer.secho(f'  Removing old environment "{venv_name}"...', nl=False, fg=typer.colors.YELLOW)
                    self.remove_environment(venv_name, verbose)
                case _:
                    typer.secho("  Aborted.", fg=typer.colors.RED)
                    raise typer.Exit(code=1)
        self._create_venv(venv_name, python, verbose)
        return venv_name

    def install_deps(self, venv_name: str, deps_path: str, verbose: bool) -> None:
        """Method to install the dependencies in the conda environment."""
        if "requirements.txt" in deps_path:
            deps_install_command = ["pip", "install", "-r", deps_path]
        elif "pyproject.toml" in deps_path:
            deps_install_command = ["pip", "install", "-e", deps_path]
        else:
            raise Exception("Only requirements.txt and pyproject.toml are supported!")

        try:
            result = subprocess.run(
                [self.path, "run", "-n", venv_name] + deps_install_command,
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to install dependencies to conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def environment_exists(self, venv_name: str) -> bool:
        """Check if a conda environment with the given name already exists."""
        try:
            result = subprocess.run(
                [self.path, "env", "list", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            envs_data = json.loads(result.stdout)
            env_names = [Path(env).name for env in envs_data.get("envs", [])]
            return venv_name in env_names
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return False

    def remove_environment(self, venv_name: str, verbose: bool = False) -> None:
        """Remove a conda environment."""
        try:
            result = subprocess.run(
                [self.path, "env", "remove", "--name", venv_name, "--yes"],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to remove conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def get_activate_cmd(self, venv_name: str) -> str:
        """Method to get the command to activate the environment."""
        return f"conda activate {venv_name}"

    def _get_path(self) -> str | None:
        """Try to find the conda executable in PATH or common install locations."""
        if conda_path := shutil.which("conda"):
            return conda_path
        candidates = (
            self._get_conda_windows_candidates()
            if platform.system() == "Windows"
            else self._get_conda_linux_mac_candidates()
        )
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)
        return None

    def _get_conda_windows_candidates(self) -> list[Path]:
        """Method to get the candidate conda paths for Windows."""
        home = Path.home()
        common_dirs = [
            home / "Anaconda3",
            home / "Miniconda3",
            home / "Miniforge3",
            Path("C:/ProgramData/Anaconda3"),
            Path("C:/ProgramData/Miniconda3"),
            Path("C:/ProgramData/Miniforge3"),
        ]
        return [d / "Scripts" / "conda.exe" for d in common_dirs]

    def _get_conda_linux_mac_candidates(self) -> list[Path]:
        """Method to get the candidate conda paths for Linux/Mac."""
        home = Path.home()
        common_dirs = [
            home / "anaconda3",
            home / "miniconda3",
            home / "miniforge3",
            Path("/opt/anaconda3"),
            Path("/opt/miniconda3"),
            Path("/opt/miniforge3"),
            home / ".conda",
        ]
        candidates = [d / "bin" / "conda" for d in common_dirs]

        # Check if there is a conda.sh for initialization
        for d in common_dirs:
            conda_sh = d / "etc" / "profile.d" / "conda.sh"
            if conda_sh.exists():
                # Try to derive the executable from the parent directory
                possible = d / "bin" / "conda"
                candidates.append(possible)

        return candidates

    def _create_venv(self, venv_name: str, python: str, verbose: bool) -> None:
        """Function to create the virtual environment using conda."""
        try:
            result = subprocess.run(
                [self.path, "create", "--name", venv_name, f"python={python}", "--yes"],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to create conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
