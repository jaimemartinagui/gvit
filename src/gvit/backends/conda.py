"""
Module with the conda backend class.
"""

import re
from pathlib import Path
import shutil
import platform
import hashlib
import os
import subprocess
import json

import typer


class CondaBackend:
    """Class for the operations with the Conda backend."""

    def __init__(self) -> None:
        self.path = self._get_path() or "conda"

    def get_unique_venv_name(self, venv_name: str) -> str:
        """
        Generate a unique environment name by adding numeric suffix if needed.
        Example: venv_name, venv_name-1, venv_name-2, etc.
        """
        if not self.venv_exists(venv_name):
            return venv_name
        counter = 1
        while self.venv_exists(f"{venv_name}-{counter}"):
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

    def create_venv(self, venv_name: str, python: str, force: bool, verbose: bool = False) -> str:
        """
        Function to create the virtual environment using conda.
        It handles the case where an environment with the same name already exists.
        """
        if self.venv_exists(venv_name):
            if force:
                typer.secho(f"⚠️  Environment '{venv_name}' already exists. Removing it...", fg=typer.colors.YELLOW)
                self.delete_venv(venv_name, verbose)
            else:
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
                        venv_name = self.get_unique_venv_name(venv_name)
                        typer.echo(f'  Using environment name "{venv_name}"...', nl=False)
                    case 2:
                        typer.echo(f'  Overwriting environment "{venv_name}"...', nl=False)
                        self.delete_venv(venv_name, verbose)
                    case _:
                        typer.secho("  Aborted!", fg=typer.colors.RED)
                        raise typer.Exit(code=1)

        self._create_venv(venv_name, python, verbose)

        return venv_name

    def install_dependencies(
        self,
        venv_name: str,
        repo_path: Path,
        deps_group_name: str,
        deps_path: Path,
        extras: list[str] | None = None,
        verbose: bool = False
    ) -> bool:
        """Method to install the dependencies from the provided deps_path."""
        typer.echo(f'  Group "{deps_group_name}"...', nl=False)
        deps_path = deps_path if deps_path.is_absolute() else repo_path / deps_path
        if not deps_path.exists():
            typer.secho(f'⚠️  "{deps_path}" not found.', fg=typer.colors.YELLOW)
            return False

        if deps_path.name == "pyproject.toml":
            install_cmd = [self.path, "run", "-n", venv_name, "pip", "install", "-e"]
            install_cmd.append(f".[{','.join(extras)}]" if extras else ".")
        elif deps_path.suffix in [".txt", ".in"]:
            install_cmd = [self.path, "run", "-n", venv_name, "pip", "install", "-r", str(deps_path)]
        else:
            typer.secho(f"❗ Unsupported dependency file format: {deps_path.name}", fg=typer.colors.RED)
            return False

        try:
            result = subprocess.run(
                install_cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
            typer.echo("✅")
            return True
        except subprocess.CalledProcessError as e:
            typer.secho(f'❗ Failed to install "{deps_path}" dependencies: {e}', fg=typer.colors.RED)
            return False

    def venv_exists(self, venv_name: str) -> bool:
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

    def delete_venv(self, venv_name: str, verbose: bool = False) -> None:
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
            typer.secho(f"❗ Failed to delete conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def get_activate_cmd(self, venv_name: str) -> str:
        """Method to get the command to activate the environment."""
        return f"conda activate {venv_name}"

    def get_venv_path(self, venv_name: str) -> str:
        """Get the absolute path to the conda environment directory."""
        try:
            result = subprocess.run(
                [self.path, "env", "list", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            envs_data = json.loads(result.stdout)
            for env_path in envs_data.get("envs", []):
                if Path(env_path).name == venv_name:
                    return env_path
            return ""
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return ""

    def get_freeze(self, venv_name: str, repo_url: str) -> str | None:
        """Method to get the complete pip freeze output for the environment (excluding repo URL)."""
        try:
            result = subprocess.run(
                [self.path, "run", "-n", venv_name, "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout:
                return None
            return re.sub(rf'^.*{repo_url}.*$\n?', '', result.stdout, flags=re.MULTILINE)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None

    def get_freeze_hash(self, venv_name: str, repo_url: str) -> str | None:
        """Method to calculate SHA256 hash (first 16 chars) of pip freeze output for the environment."""
        freeze = self.get_freeze(venv_name, repo_url)
        return hashlib.sha256(freeze.encode()).hexdigest()[:16] if freeze else None

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
            typer.secho(f"❗ Failed to create conda environment:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
