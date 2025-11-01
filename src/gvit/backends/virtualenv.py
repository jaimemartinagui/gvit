"""
Module with the virtualenv backend class.
"""

import re
from pathlib import Path
import subprocess
import platform
import shutil
import hashlib

import typer


class VirtualenvBackend:
    """Class for operations with the virtualenv backend."""

    def create_venv(
        self, venv_name: str, repo_path: Path, python: str, force: bool, verbose: bool = False
    ) -> str:
        """Create a virtual environment in the repository directory using virtualenv."""
        if self.venv_exists(venv_name, repo_path):
            if force:
                typer.secho(f'⚠️  Environment "{venv_name}" already exists. Removing it...', fg=typer.colors.YELLOW)
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
                    typer.secho("  Aborted!", fg=typer.colors.RED)
                    raise typer.Exit(code=1)

        self._create_venv(str(repo_path / venv_name), python, verbose)
        self._ensure_gitignore(venv_name, repo_path)

        return venv_name

    def generate_unique_venv_registry_name(self, venv_path: Path) -> str:
        """
        Generate a unique registry name for virtualenv environments.
        Uses the project name (parent of the venv_path) + short hash of absolute path to avoid collisions.
        Example: myrepo-a1b2c3
        """
        path_hash = hashlib.sha256(str(venv_path).encode()).hexdigest()[:6]
        return f"{venv_path.parent.name}-{path_hash}"

    def is_available(self) -> bool:
        """Check if virtualenv is available and functional."""
        try:
            result = subprocess.run(
                ["virtualenv", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return "virtualenv" in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_dependencies(
        self,
        venv_name: str,
        repo_path: Path,
        deps_group_name: str,
        deps_path: Path,
        extras: list[str] | None = None,
        verbose: bool = False
    ) -> bool:
        """Install dependencies in the virtualenv using pip."""
        typer.echo(f'  Group "{deps_group_name}"...', nl=False)

        deps_path = deps_path if deps_path.is_absolute() else repo_path / deps_path
        if not deps_path.exists():
            typer.secho(f'⚠️  "{deps_path}" not found.', fg=typer.colors.YELLOW)
            return False

        pip_path = self._get_pip_executable_path(repo_path / venv_name)
        if deps_path.name == "pyproject.toml":
            install_cmd = [pip_path, "install", "-e"]
            install_cmd.append(f".[{','.join(extras)}]" if extras else ".")
        elif deps_path.suffix in [".txt", ".in"]:
            install_cmd = [pip_path, "install", "-r", str(deps_path)]
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

    def venv_exists(self, venv_name: str, repo_path: Path) -> bool:
        """Check if the virtualenv directory exists and is valid."""
        venv_path = repo_path / venv_name
        if not venv_path.exists():
            return False
        return (
            (venv_path / "Scripts" / "python.exe").exists()
            if platform.system() == "Windows"
            else (venv_path / "bin" / "python").exists()
        )

    def delete_venv(self, venv_name: str, repo_path: Path, verbose: bool = False) -> None:
        """Remove the virtualenv directory."""
        venv_path = repo_path / venv_name
        if not venv_path.exists():
            if verbose:
                typer.echo(f"Virtualenv directory {venv_path} does not exist, nothing to delete.")
            return None
        try:
            shutil.rmtree(venv_path)
            if verbose:
                typer.echo(f"Deleted virtualenv directory: {venv_path}")
        except Exception as e:
            typer.secho(f"❗ Failed to delete virtualenv directory: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def get_activate_cmd(self, venv_path: str, relative: bool = True) -> str:
        """Get the command to activate the virtual environment."""
        venv_path = Path(venv_path).name if relative else venv_path
        return (
            f"{venv_path}\\Scripts\\activate"
            if platform.system() == "Windows"
            else f"source {venv_path}/bin/activate"
        )

    def get_venv_path(self, venv_name: str, repo_path: Path) -> str:
        """Get the absolute path to the virtualenv directory."""
        return str((repo_path / venv_name).resolve())

    def get_freeze(self, venv_name: str, repo_path: Path, repo_url: str) -> str | None:
        """Method to get the complete pip freeze output for the environment (excluding repo URL)."""
        try:
            venv_path = self.get_venv_path(venv_name, repo_path)
            pip_path = self._get_pip_executable_path(Path(venv_path))
            result = subprocess.run(
                [pip_path, "freeze"],
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
        """Create the virtual environment using virtualenv."""
        try:
            result = subprocess.run(
                ["virtualenv", "-p", f"python{python}", venv_path],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to create virtualenv:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def _get_pip_executable_path(self, venv_path: Path) -> str:
        """Get the pip executable path inside the virtualenv."""
        pip_executable_path = (
            venv_path / "Scripts" / "pip.exe"
            if platform.system() == "Windows"
            else venv_path / "bin" / "pip"
        )
        return str(pip_executable_path)

    def _ensure_gitignore(self, venv_name: str, repo_path: Path) -> None:
        """Add virtualenv directory to .gitignore if not already present."""
        gitignore_path = repo_path / ".gitignore"
        lines = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
        if venv_name not in lines and f"/{venv_name}" not in lines:
            lines.append(venv_name)
            gitignore_path.write_text("\n".join(lines) + "\n")
