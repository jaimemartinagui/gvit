"""
Module with the Git class.
"""

import subprocess
from pathlib import Path

import typer


class Git:
    """Class with the methods to run Git commands."""

    def clone(
        self, repo_url: str, target_dir: str, extra_args: list[str] | None = None, verbose: bool = False
    ) -> None:
        """Function to clone the repository."""
        typer.echo(f"- Cloning repository {repo_url}...", nl=False)
        try:
            result = subprocess.run(
                ["git", "clone", repo_url, target_dir] + (extra_args or []),
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"❗ Git clone failed:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def pull(self, repo_dir: str, extra_args: list[str] | None = None, verbose: bool = False) -> None:
        """Run git pull command."""
        try:
            result = subprocess.run(
                ["git", "pull"] + (extra_args or []),
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"❗ Git pull failed:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def commit(self, repo_dir: str, extra_args: list[str] | None = None, verbose: bool = False) -> None:
        """Run git commit command."""
        try:
            result = subprocess.run(
                ["git", "commit"] + (extra_args or []),
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if result.stdout:
                typer.echo(result.stdout)
            if verbose and result.stderr:
                typer.echo(result.stderr)
        except subprocess.CalledProcessError as e:
            # Git commit can fail for valid reasons (nothing to commit, etc.)
            typer.secho(f"❗ Git commit failed:\n{e.stdout}{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=e.returncode)

    def init(self, target_dir: str, extra_args: list[str] | None = None, verbose: bool = False) -> None:
        """Function to initialize the Git repository."""
        try:
            result = subprocess.run(
                ["git", "init"] + (extra_args or []),
                cwd=target_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"❗ Git init failed:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def add_remote(self, target_dir: str, remote_url: str, verbose: bool = False) -> None:
        """Add remote origin to the Git repository."""
        try:
            result = subprocess.run(
                ["git", "remote", "add", "origin", remote_url],
                cwd=target_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            typer.echo("✅")
            if verbose and result.stdout:
                typer.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            typer.secho(f"❗ Failed to add remote:\n{e.stderr}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    def get_remote_url(self, repo_dir: str) -> str:
        """Get the remote URL of the repository if it exists."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def get_staged_deps_files(self, repo_path: Path) -> list[str]:
        """Get dependency files that are currently staged."""
        common_deps_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "requirements-test.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
        ]
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            staged_files = result.stdout.strip().split("\n")
            return [f for f in staged_files if any(dep in f for dep in common_deps_files)]
        except subprocess.CalledProcessError:
            return []
