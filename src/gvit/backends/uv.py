"""
Module with the uv backend class.
"""

import re
from pathlib import Path
import subprocess
import sys
import platform
import shutil
import hashlib

import typer

from gvit.error_handler import exit_with_error


class UvBackend:

    def __init__(self) -> None:
        pass

    def create_venv(
        self, venv_name: str, repo_path: Path, python: str, force: bool, verbose: bool = False
    ) -> str:
        """Create a virtual environment in the repository directory."""
        if self.venv_exists(venv_name, repo_path):
            if force:
                typer.secho(f'⚠️  Environment "{venv_name}" already exists. Deleting it...', fg=typer.colors.YELLOW)
                self.delete_venv(venv_name, repo_path)
            else:
                typer.secho(f'\n  ⚠️  Environment "{venv_name}" already exists. What would you like to do?', fg=typer.colors.YELLOW)
                choice = typer.prompt(
                    "    [1] Overwrite existing environment\n"
                    "    [2] Abort\n"
                    "  Select option",
                    type=int,
                    default=1
                )
                if choice == 1:
                    typer.echo(f'  Overwriting environment "{venv_name}"...', nl=False)
                    self.delete_venv(venv_name, repo_path)
                else:
                    error_msg = "  Aborted!"
                    typer.secho(error_msg, fg=typer.colors.RED)
                    exit_with_error(error_msg)

        self._create_venv(str(repo_path / venv_name), python, verbose)
        self._ensure_gitignore(venv_name, repo_path)

        return venv_name

    def generate_unique_venv_registry_name(self, venv_path: Path) -> str:
        """
        Generate a unique registry name for venv environments.
        Uses the project name (parent of the venv_path) + short hash of absolute path to avoid collisions.
        Example: myrepo-a1b2c3
        """
        path_hash = hashlib.sha256(str(venv_path).encode()).hexdigest()[:6]
        return f"{venv_path.parent.name}-{path_hash}"

    def is_uv_installed(self, venv_path: Path) -> bool:
        """Method to check if uv is installed (globally or locally)."""
        uv_global_path = shutil.which("uv")
        uv_executable_path = (
            venv_path / "Scripts" / "uv.exe"
            if platform.system() == "Windows"
            else venv_path / "bin" / "uv"
        )
        return bool(uv_global_path) or uv_executable_path.exists()

    def install_dependencies(
        self,
        venv_name: str,
        repo_path: Path,
        deps_group_name: str,
        deps_path: Path,
        extras: list[str] | None = None,
        verbose: bool = False
    ) -> bool:
        """Install dependencies in the venv using pip."""
        typer.echo(f'  Group "{deps_group_name}"...', nl=False)

        deps_path = deps_path if deps_path.is_absolute() else repo_path / deps_path
        if not deps_path.exists():
            typer.secho(f'⚠️  "{deps_path}" not found.', fg=typer.colors.YELLOW)
            return False

        install_cmd = self._get_install_cmd(repo_path / venv_name, deps_path, extras)
        if not install_cmd:
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

    def venv_exists(self, venv_name: str, repo_path: Path) -> bool:
        """Check if the venv directory exists and is valid."""
        venv_path = repo_path / venv_name
        if not venv_path.exists():
            return False
        return (
            (venv_path / "Scripts" / "python.exe").exists()
            if platform.system() == "Windows"
            else (venv_path / "bin" / "python").exists()
        )

    def delete_venv(self, venv_name: str, repo_path: Path, verbose: bool = False) -> None:
        """Remove the venv directory."""
        venv_path = repo_path / venv_name
        if not venv_path.exists():
            if verbose:
                typer.echo(f"Venv directory {venv_path} does not exist, nothing to delete.")
            return None
        try:
            shutil.rmtree(venv_path)
            if verbose:
                typer.echo(f"Deleted venv directory: {venv_path}")
        except Exception as e:
            error_msg = f"❗ Failed to delete venv directory: {e}"
            typer.secho(error_msg, fg=typer.colors.RED)
            exit_with_error(error_msg)

    def get_activate_cmd(self, venv_path: str, relative: bool = True) -> str:
        """Get the command to activate the virtual environment."""
        venv_path = Path(venv_path).name if relative else venv_path
        return (
            f"{venv_path}\\Scripts\\activate"
            if platform.system() == "Windows"
            else f"source {venv_path}/bin/activate"
        )

    def get_deactivate_cmd(self) -> str:
        """Get the command to deactivate the virtual environment."""
        return "deactivate"

    def get_venv_path(self, venv_name: str, repo_path: Path) -> str:
        """Get the absolute path to the venv directory."""
        return str((repo_path / venv_name).resolve())

    def get_freeze(self, venv_name: str, repo_path: Path, repo_url: str) -> str | None:
        """Method to get the complete pip freeze output for the environment (excluding repo URL)."""
        try:
            venv_path = self.get_venv_path(venv_name, repo_path)
            python_path = self._get_python_executable_path(Path(venv_path))
            result = subprocess.run(
                ["uv", "pip", "freeze", "--python", python_path],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout:
                return None
            return re.sub(rf'^.*{repo_url}.*$\n?', '', result.stdout, flags=re.MULTILINE)
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None

    def get_freeze_hash(self, venv_name: str, repo_path: Path, repo_url: str) -> str | None:
        """Method to calculate SHA256 hash (first 16 chars) of pip freeze output for the environment."""
        freeze = self.get_freeze(venv_name, repo_path, repo_url)
        return hashlib.sha256(freeze.encode()).hexdigest()[:16] if freeze else None

    def _create_venv(self, venv_path: str, python: str, verbose: bool = False) -> None:
        """Create the virtual environment using uv."""
        try:
            result = subprocess.run(
                ["uv", "venv", venv_path, "--python", python],
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = f"❗ Failed to create venv:\n{e.stderr}"
            typer.secho(error_msg, fg=typer.colors.RED)
            exit_with_error(error_msg)

    def _get_install_cmd(
        self, venv_path: Path, deps_path: Path, extras: list[str] | None
    ) -> list[str] | None:
        """Method to get the install command."""
        python_path = self._get_python_executable_path(venv_path)
        install_cmd = ["uv", "pip", "install", "-p", python_path]
        if deps_path.name == "pyproject.toml":
            install_cmd.extend(["-e", f".[{','.join(extras)}]" if extras else "."])
        elif deps_path.suffix in [".txt", ".in"]:
            install_cmd.extend(["-r", str(deps_path)])
        else:
            typer.secho(f"❗ Unsupported dependency file format: {deps_path.name}", fg=typer.colors.RED)
            return None
        return install_cmd

    def _get_python_executable_path(self, venv_path: Path) -> str:
        """Get the python executable path inside the venv."""
        pip_executable_path = (
            venv_path / "Scripts" / "python.exe"
            if platform.system() == "Windows"
            else venv_path / "bin" / "python"
        )
        return str(pip_executable_path)

    def _ensure_gitignore(self, venv_name: str, repo_path: Path) -> None:
        """Add venv directory to .gitignore if not already present."""
        gitignore_path = repo_path / ".gitignore"
        lines = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
        if venv_name not in lines and f"/{venv_name}" not in lines:
            lines.append(venv_name)
            gitignore_path.write_text("\n".join(lines) + "\n")
