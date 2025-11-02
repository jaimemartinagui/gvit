"""
Module with the Git class.
"""

import sys

import subprocess
from pathlib import Path

import typer


class Git:
    """Class with the methods to run Git commands."""

    def run(self, args: list[str]) -> None:
        """Execute any command with git."""
        try:
            # Run git command directly, inheriting stdin/stdout/stderr
            # Don not raise, let git handle its own errors
            # Exit with git's exit code
            result = subprocess.run(["git"] + args, check=False)
            sys.exit(result.returncode)
        except FileNotFoundError:
            typer.secho("\nError: git is not installed or not in PATH.", fg=typer.colors.RED, err=True)
            sys.exit(1)
        except Exception as e:
            typer.secho(f"\nError executing git command: {e}", fg=typer.colors.RED, err=True)
            sys.exit(1)

    def command_exists(self, command: str) -> bool:
        """Method to check if a Git command exists (exit code 0) or not."""
        result = subprocess.run(
            ["git", command, "--help"],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

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

    def status(self, repo_path: Path, extra_args: list[str] | None = None) -> None:
        """Show git status output with color highlighting."""
        try:
            result = subprocess.run(
                ["git", "status"] + (extra_args or []),
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_section = None
            sections = {
                "staged": "Changes to be committed:",
                "unstaged": "Changes not staged for commit:",
                "untracked": "Untracked files:"
            }
            for line in result.stdout.strip().split("\n"):
                if match := next((k for k, v in sections.items() if v in line), None):
                    current_section = match
                # Section headers
                if line.strip().startswith(tuple(sections.values())):
                    typer.secho(f"  {line}", fg=typer.colors.YELLOW, bold=True)
                # Staged files (new, modified, deleted) - colored GREEN
                elif current_section == "staged" and "new file:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.GREEN)
                elif current_section == "staged" and "modified:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.GREEN)
                elif current_section == "staged" and "deleted:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.GREEN)
                elif current_section == "staged" and "renamed:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.GREEN)
                # Unstaged files (modified, deleted) - colored RED
                elif current_section == "unstaged" and "modified:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.RED)
                elif current_section == "unstaged" and "deleted:" in line:
                    typer.secho(f"  {line}", fg=typer.colors.RED)
                # Untracked files - colored RED
                elif line.strip() and not line.strip().startswith(("(", "no changes", "nothing to commit")):
                    # Check if it's likely a file path (starts with tab or spaces followed by text)
                    if line.startswith(("\t", "  ")) and not "use" in line.lower():
                        typer.secho(f"  {line}", fg=typer.colors.RED)
                    else:
                        typer.echo(f"  {line}")
                # Hints and other text
                elif "use" in line.lower() or "(" in line:
                    typer.secho(f"  {line}", fg=typer.colors.BRIGHT_BLACK, dim=True)
                # "no changes" / "nothing to commit"
                elif "no changes" in line.lower() or "nothing to commit" in line.lower():
                    typer.secho(f"  {line}", fg=typer.colors.BRIGHT_BLACK)
                else:
                    typer.echo(f"  {line}")
        except subprocess.CalledProcessError as e:
            typer.secho(f"  ❗ Failed to get git status: {e}", fg=typer.colors.RED)

    def resolve_alias(self, alias: str) -> str:
        """Resolve a git alias to its underlying command."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", f"alias.{alias}"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                # Return the resolved alias (just the first word if it's a compound command)
                return result.stdout.strip().split()[0]
        except Exception:
            pass
        return alias

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
