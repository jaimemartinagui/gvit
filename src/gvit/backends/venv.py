"""
Module with the venv backend class.
"""

from pathlib import Path
import subprocess
import sys
import platform
import shutil
import hashlib

import typer


class VenvBackend:
    """Class for operations with the venv backend."""

    def create_venv(
        self, venv_name: str, repo_path: Path, python: str, force: bool, verbose: bool = False
    ) -> str:
        """Create a virtual environment in the repository directory."""
        venv_path = repo_path / venv_name

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

        self._create_venv(venv_path, python, verbose)
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

        venv_path = repo_path / venv_name
        pip_executable = self._get_pip_executable(venv_path)
        
        if deps_path.name == "pyproject.toml":
            install_cmd = [str(pip_executable), "install", "-e"]
            install_cmd.append(f".[{','.join(extras)}]" if extras else ".")
        elif deps_path.suffix in [".txt", ".in"]:
            install_cmd = [str(pip_executable), "install", "-r", str(deps_path)]
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
            typer.secho(f"❗ Failed to delete venv directory: {e}", fg=typer.colors.RED)
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
        """Get the absolute path to the venv directory."""
        return str((repo_path / venv_name).resolve())

    def _create_venv(self, venv_path: Path, python: str, verbose: bool = False) -> None:
        """Create the virtual environment using the venv module or python -m venv."""
        try:
            python_cmd = self._get_python_cmd(python)
            result = subprocess.run(
                [python_cmd, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Failed to create venv:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def _get_python_cmd(self, python_version: str) -> str:
        """
        Get the python command for the specified version.
        Tries: python{version}, python{major}.{minor}, python3, python
        """
        # Parse version (e.g., "3.11" -> try python3.11, python3, python)
        candidates = []
        
        if "." in python_version:
            # Full version specified (e.g., "3.11")
            candidates.append(f"python{python_version}")
            major = python_version.split(".")[0]
            candidates.append(f"python{major}")
        else:
            # Just major version (e.g., "3")
            candidates.append(f"python{python_version}")
        
        # Fallbacks
        candidates.extend(["python3", "python"])
        
        for cmd in candidates:
            if shutil.which(cmd):
                # Verify it matches the requested version
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    version_str = result.stdout.strip()
                    # Check if version matches (fuzzy match on major.minor)
                    if python_version in version_str or python_version.split(".")[0] in version_str:
                        return cmd
                except subprocess.CalledProcessError:
                    continue
        
        # If no match found, use current Python
        typer.secho(f"⚠️  Python {python_version} not found, using current Python ({sys.version.split()[0]})", fg=typer.colors.YELLOW)
        return sys.executable

    def _get_pip_executable(self, venv_path: Path) -> Path:
        """Get the pip executable path inside the venv."""
        return venv_path / "Scripts" / "pip.exe" if platform.system() == "Windows" else venv_path / "bin" / "pip"

    def _ensure_gitignore(self, venv_name: str, repo_path: Path) -> None:
        """Add venv directory to .gitignore if not already present."""
        gitignore_path = repo_path / ".gitignore"
        lines = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
        if venv_name not in lines and f"/{venv_name}" not in lines:
            lines.append(venv_name)
            gitignore_path.write_text("\n".join(lines) + "\n")
