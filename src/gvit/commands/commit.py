"""
Module for the "gvit commit" command.
"""

from pathlib import Path
# import re

import typer
# import toml

from gvit.env_registry import EnvRegistry
from gvit.utils.utils import load_local_config, get_verbose
from gvit.utils.validators import validate_directory, validate_git_repo
from gvit.backends.common import get_freeze, get_freeze_hash, get_freeze_diff, show_freeze_diff
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
            added, removed, changed = get_freeze_diff(stored_freeze, current_freeze)
            show_freeze_diff(added, removed, changed)
            _ask_user()

            # deps_files_paths = {
            #     name: repo_path / Path(path)
            #     for name, path in env.get("deps", {}).items() 
            #     if name != "installed" and isinstance(path, str)
            # }
            # if deps_files_paths:
            #     typer.echo("- Validating dependency files...", nl=False)
            #     validation_issues = _validate_deps_files(deps_files_paths, added, removed, changed)
            #     if not validation_issues:
            #         typer.secho("dependency files are in sync with installed packages. ✅\n", fg=typer.colors.GREEN)
            #     else:
            #         typer.secho("\n  ⚠️  Issues found in dependency files:", fg=typer.colors.YELLOW)
            #         for issue in validation_issues:
            #             typer.echo(f"    • {issue}")
            #         _ask_user()

    # 7. Execute git commit
    typer.echo("\n- Running git commit...", nl=False)
    git.commit(str(target_dir_), ctx.args, verbose)

    typer.echo("🎉 Commit successful!")


def _ask_user() -> None:
    """Function to ask the user what to do.º"""
    typer.echo("\n  What would you like to do?")
    choice = typer.prompt(
        "    [1] Continue with commit\n"
        "    [2] Abort commit\n"
        "  Select option",
        type=int,
        default=2
    )
    if choice != 1:
        typer.secho("❗ Commit aborted.", fg=typer.colors.RED)
        raise typer.Exit(code=1)


# def _validate_deps_files(
#     deps_files_paths: dict[str, Path],
#     added: dict[str, str],
#     removed: dict[str, str],
#     changed: dict[str, tuple[str, str]]
# ) -> list[str]:
#     """Validate that dependency files reflect the package changes."""
#     issues = []

#     # Parse all dependency files
#     all_declared_packages = set()
#     for _, deps_path in deps_files_paths.items():
#         if not deps_path.exists():
#             continue
#         declared = _parse_deps_file(deps_path)
#         all_declared_packages.update(declared.keys())

#     # Check for added packages not in any deps file
#     missing_additions = set(added.keys()) - all_declared_packages
#     if missing_additions:
#         pkg_list = ", ".join(sorted(list(missing_additions)))
#         issues.append(f"Added packages not declared: {pkg_list}")

#     # Check for removed packages still in deps files
#     still_declared_removals = set(removed.keys()) & all_declared_packages
#     if still_declared_removals:
#         pkg_list = ", ".join(sorted(list(still_declared_removals)))
#         issues.append(f"Removed packages still declared: {pkg_list}")

#     # Check for changed packages with pinned versions not updated
#     for pkg, (old_ver, new_ver) in changed.items():
#         if pkg in all_declared_packages:
#             # Check if any deps file has the old pinned version
#             for _, deps_path in deps_files_paths.items():
#                 if not deps_path.exists():
#                     continue
#                 declared = _parse_deps_file(deps_path)
#                 if pkg in declared and declared[pkg] == old_ver:
#                     issues.append(f"{pkg}: version changed to {new_ver} but {deps_path.name} still has {old_ver}")
#                     break

#     return issues


# def _parse_deps_file(deps_path: Path) -> dict[str, str | None]:
#     """Parse a dependency file and return {package: version} dict."""
#     if deps_path.name == "pyproject.toml":
#         return _parse_pyproject_toml(deps_path)
#     if deps_path.suffix in [".txt", ".in"]:
#         return _parse_requirements_txt(deps_path)
#     return {}


# def _parse_pyproject_toml(pyproject_path: Path) -> dict[str, str | None]:
#     """Parse pyproject.toml and extract all dependencies."""
#     packages = {}
#     try:
#         data = toml.load(pyproject_path)
#         base_deps = data.get("project", {}).get("dependencies", [])
#         for dep in base_deps:
#             pkg, ver = _parse_dep_specifier(dep)
#             packages[pkg] = ver
#         optional_deps = data.get("project", {}).get("optional-dependencies", {})
#         for group_deps in optional_deps.values():
#             for dep in group_deps:
#                 pkg, ver = _parse_dep_specifier(dep)
#                 packages[pkg] = ver
#     except Exception:
#         pass
#     return packages


# def _parse_requirements_txt(req_path: Path) -> dict[str, str | None]:
#     """Parse requirements.txt file."""
#     packages = {}
#     try:
#         for line in req_path.read_text().splitlines():
#             line = line.strip()
#             if not line or line.startswith("#"):
#                 continue
#             # Skip options like -e, --index-url, etc.
#             if line.startswith("-"):
#                 continue
#             pkg, ver = _parse_dep_specifier(line)
#             packages[pkg] = ver
#     except Exception:
#         pass
#     return packages


# def _parse_dep_specifier(spec: str) -> tuple[str, str | None]:
#     """Parse a dependency specifier and return (package_name, version)."""
#     # Remove extras like package[extra]
#     spec = re.sub(r'\[.*?\]', '', spec).strip()
#     # Handle different version specifiers
#     if "==" in spec:
#         pkg, ver = spec.split("==", 1)
#         return pkg.strip().lower(), ver.strip()
#     elif ">=" in spec or "<=" in spec or "~=" in spec or ">" in spec or "<" in spec or "!=" in spec:
#         # Non-pinned version, extract package name
#         pkg = re.split(r'[><=!~]', spec)[0].strip()
#         return pkg.lower(), None
#     else:
#         # No version specifier
#         return spec.strip().lower(), None
