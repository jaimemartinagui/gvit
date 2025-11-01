"""
Module for the "gvit commit" command.
"""

from pathlib import Path

import typer

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, get_verbose
from gvit.utils.validators import validate_directory, validate_git_repo
from gvit.backends.common import get_freeze, get_freeze_hash
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

    current_freeze_hash = get_freeze_hash(venv_name, repo_path, env["repository"]["url"], backend)

    if current_freeze_hash == stored_freeze_hash:
        typer.secho("dependencies are in sync ✅", fg=typer.colors.GREEN)
    else:
        typer.secho("⚠️  Dependency drift detected!", fg=typer.colors.YELLOW)
        typer.echo("  The installed packages differ from the last tracked state.\n")

        stored_freeze = env.get("deps", {}).get("installed", {}).get("_freeze", "")
        current_freeze = get_freeze(venv_name, repo_path, env["repository"]["url"], backend)

        if stored_freeze and current_freeze:
            added, removed, changed = _get_freeze_diff(stored_freeze, current_freeze)
            _show_freeze_diff(added, removed, changed)

        typer.echo("  What would you like to do?")
        choice = typer.prompt(
            "    [1] Continue with commit (I've updated the dependency files)\n"
            "    [2] Abort commit\n"
            "  Select option",
            type=int,
            default=2
        )
        if choice == 1:
            typer.echo("✅ Continuing with commit...\n")
        else:
            typer.secho("❗ Commit aborted.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    # 7. Execute git commit
    typer.echo("\n- Running git commit...", nl=False)
    git.commit(str(target_dir_), ctx.args, verbose)

    typer.echo("🎉 Commit successful!")


def _get_freeze_diff(
    stored_freeze: str, current_freeze: str
) -> tuple[dict[str, str], dict[str, str], dict[str, tuple[str, str]]]:
    """Get the added, removed and modified packages."""
    def parse_freeze(text: str) -> dict[str, str]:
        """Convert a pip freeze text into a {package: version} dict."""
        packages = {}
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                packages[pkg.lower()] = ver
            else:
                # handle non-standard lines (like editable installs or VCS)
                packages[line.lower()] = None
        return packages

    old = parse_freeze(stored_freeze)
    new = parse_freeze(current_freeze)

    added = {pkg: new[pkg] for pkg in new.keys() - old.keys()}
    removed = {pkg: old[pkg] for pkg in old.keys() - new.keys()}
    changed = {pkg: (old[pkg], new[pkg]) for pkg in old.keys() & new.keys() if old[pkg] != new[pkg]}

    return added, removed, changed


def _show_freeze_diff(added: dict[str, str], removed: dict[str, str], changed: dict[str, tuple[str, str]]) -> None:
    """Show summary of package changes between two pip freeze outputs."""
    if added:
        typer.echo("  📦 Added packages:")
        for pkg, ver in sorted(added.items()):
            typer.secho(f"    + {pkg}=={ver}" if ver else f"  + {pkg}", fg=typer.colors.GREEN)
        typer.echo()

    if removed:
        typer.echo("  📦 Removed packages:")
        for pkg, ver in sorted(removed.items()):
            typer.secho(f"    - {pkg}=={ver}" if ver else f"  - {pkg}", fg=typer.colors.RED)
        typer.echo()

    if changed:
        typer.echo("  📦 Package versions changed:")
        for pkg, (old_v, new_v) in sorted(changed.items()):
            typer.secho(f"    ~ {pkg}: {old_v} → {new_v}", fg=typer.colors.YELLOW)
        typer.echo()

    if not (added or removed or changed):
        typer.secho("✅ No changes detected.", fg=typer.colors.GREEN)
