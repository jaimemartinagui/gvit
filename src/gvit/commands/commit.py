"""
Module for the "gvit commit" command.
"""

import subprocess
from pathlib import Path
from difflib import unified_diff

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, get_verbose
from gvit.utils.validators import validate_directory, validate_git_repo
from gvit.backends.conda import CondaBackend
from gvit.backends.venv import VenvBackend
from gvit.backends.common import get_freeze_hash
from gvit.git import Git


def commit(
    ctx: typer.Context,
    target_dir: str = typer.Option(".", "--target-dir", "-t", help="Directory of the repository (defaults to current directory)."),
    skip_validation: bool = typer.Option(False, "--skip-validation", "-s", help="Skip dependency validation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Commit changes with automatic dependency validation.

    Validates that installed packages match the declared dependencies before committing.
    If drift is detected, shows the diff and asks for confirmation.

    Any extra options will be passed directly to `git commit`.

    Long options do not conflict between `gvit commit` and `git commit`.

    Short options might conflict; in that case, use the long form for the `git commit` options.

    Examples:

    -> gvit commit -m "Add new feature"

    -> gvit commit --amend

    -> gvit commit -a -m "Quick fix"
    """
    # 1. Resolve and validate directory
    target_dir_ = Path(target_dir).resolve()
    validate_directory(target_dir_)

    # 2. Check if it is a git repository
    validate_git_repo(target_dir_)

    # 3. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 4. Get environment from registry (search by repo path)
    typer.echo("- Searching for the environment in the registry...", nl=False)
    env_registry = EnvRegistry()
    envs = [env for env in env_registry.get_environments() if Path(env['repository']['path']) == target_dir_]
    git = Git()
    if envs:
        env = envs[0]
        registry_name = env["environment"]["name"]
        venv_name = Path(env["environment"]["path"]).name
        backend = env["environment"]["backend"]
        repo_path = Path(env["repository"]["path"])
        repo_url = env["repository"]["url"]
        stored_freeze_hash = env.get("deps", {}).get("installed", {}).get("_freeze_hash")
        typer.secho(f'environment found: "{registry_name}". ✅', fg=typer.colors.GREEN)
    else:
        env = None
        stored_freeze_hash = None
        typer.secho("⚠️  No tracked environment found for this repository.", fg=typer.colors.YELLOW)
        typer.echo("\n- Skipping dependency validation. Use `gvit setup` to track this repository.\n")

    # 5. Skip dependency validation and commit
    if not stored_freeze_hash:
        typer.secho(
            "\n⚠️  No freeze hash found in registry. Dependencies were installed without tracking.\n",
            fg=typer.colors.YELLOW
        )
    if skip_validation or not env or not stored_freeze_hash:
        typer.echo("- Running git commit...", nl=False)
        git.commit(str(target_dir_), ctx.args, verbose)
        typer.echo("🎉 Commit successful!")
        return None

    # 6. Validate dependencies
    typer.echo("\n- Validating dependencies...", nl=False)

    current_freeze_hash = get_freeze_hash(venv_name, repo_path, repo_url, backend)

    if current_freeze_hash == stored_freeze_hash:
        typer.secho("dependencies are in sync ✅", fg=typer.colors.GREEN)
    else:
        typer.secho("⚠️  Dependency drift detected!", fg=typer.colors.YELLOW)
        typer.echo("The installed packages differ from the last tracked state.\n")

        # Get the diff
        stored_freeze = _get_freeze_output(venv_name, repo_path, backend, stored_freeze_hash)
        current_freeze = _get_freeze_output_current(venv_name, repo_path, backend)

        if stored_freeze and current_freeze:
            _show_freeze_diff(stored_freeze, current_freeze)

        # Check if dependency files are staged
        staged_deps_files = _get_staged_deps_files(target_dir_)
        if staged_deps_files:
            typer.echo(f"📝 Dependency files in staging area: {', '.join(staged_deps_files)}\n")
        else:
            typer.secho(
                "⚠️  No dependency files found in staging area.",
                fg=typer.colors.YELLOW
            )
            typer.echo("Did you forget to update requirements.txt or pyproject.toml?\n")

        # Ask user what to do
        typer.echo("What would you like to do?")
        choice = typer.prompt(
            "  [1] Continue with commit (I've updated the dependency files)\n"
            "  [2] Show full pip freeze diff\n"
            "  [3] Abort commit\n"
            "Select option",
            type=int,
            default=3
        )

        match choice:
            case 1:
                typer.echo("✅ Continuing with commit...\n")
            case 2:
                _show_full_freeze_diff(stored_freeze, current_freeze)
                # Ask again after showing diff
                if not typer.confirm("\nDo you want to continue with the commit?", default=False):
                    typer.secho("❌ Commit aborted.", fg=typer.colors.RED)
                    raise typer.Exit(code=1)
            case _:
                typer.secho("❌ Commit aborted.", fg=typer.colors.RED)
                raise typer.Exit(code=1)

    # 7. Execute git commit
    typer.echo("\n- Running git commit...", nl=False)
    git.commit(str(target_dir_), ctx.args, verbose)

    typer.echo("🎉 Commit successful!")


def _get_freeze_output_current(venv_name: str, repo_path: Path, backend: str) -> list[str] | None:
    """Get current pip freeze output as list of lines."""
    try:
        if backend == "conda":
            conda_backend = CondaBackend()
            result = subprocess.run(
                [conda_backend.path, "run", "-n", venv_name, "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
        elif backend in ["venv", "virtualenv"]:
            venv_backend = VenvBackend()
            pip_path = venv_backend._get_pip_executable_path(repo_path / venv_name)
            result = subprocess.run(
                [pip_path, "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            return None

        return sorted([line for line in result.stdout.strip().split("\n") if line])
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        return None


def _get_freeze_output(venv_name: str, repo_path: Path, backend: str, freeze_hash: str) -> list[str] | None:
    """
    Get stored pip freeze output from registry or reconstruct from current state.
    Since we only store the hash, we return current freeze as proxy.
    In practice, we can't recover the old freeze, so we return None.
    """
    # Note: We can't recover the old freeze output from just the hash
    # This is a limitation - we'd need to store the full freeze output
    # For now, return None to skip detailed diff
    return None


def _show_freeze_diff(stored_freeze: list[str] | None, current_freeze: list[str] | None) -> None:
    """Show summary of package changes."""
    if not current_freeze:
        typer.echo("Unable to retrieve current package list.\n")
        return

    # Since we can't get stored_freeze from hash alone, show what changed conceptually
    typer.echo("The hash of installed packages has changed.")
    typer.echo("This means packages were added, removed, or updated.\n")


def _show_full_freeze_diff(stored_freeze: list[str] | None, current_freeze: list[str] | None) -> None:
    """Show detailed diff of pip freeze outputs."""
    if not stored_freeze or not current_freeze:
        typer.echo("\n📦 Current installed packages:")
        if current_freeze:
            for line in current_freeze:
                typer.echo(f"  {line}")
        else:
            typer.echo("  Unable to retrieve package list.")
        return

    typer.echo("\n📦 Package changes:")
    diff = unified_diff(
        stored_freeze,
        current_freeze,
        fromfile="stored (last tracked)",
        tofile="current (now)",
        lineterm=""
    )

    diff_lines = list(diff)
    if not diff_lines:
        typer.echo("  No changes detected (identical)")
    else:
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                typer.secho(f"  {line}", fg=typer.colors.GREEN)
            elif line.startswith("-") and not line.startswith("---"):
                typer.secho(f"  {line}", fg=typer.colors.RED)
            else:
                typer.echo(f"  {line}")


def _get_staged_deps_files(repo_path: Path) -> list[str]:
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
