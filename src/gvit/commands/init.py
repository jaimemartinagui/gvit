"""
Module for the "gvit init" command.
"""

from pathlib import Path

import typer

from gvit.utils.utils import (
    load_local_config,
    load_repo_config,
    get_backend,
    get_python,
    get_package_manager,
    get_verbose,
)
from gvit.utils.validators import validate_backend, validate_python, validate_package_manager, validate_directory
from gvit.env_registry import EnvRegistry
from gvit.utils.globals import SUPPORTED_BACKENDS, SUPPORTED_PACKAGE_MANAGERS
from gvit.backends.common import create_venv, install_dependencies, show_summary_message
from gvit.git import Git


def init(
    ctx: typer.Context,
    target_dir: str = typer.Option(".", "--target-dir", "-t", help="Directory to initialize (defaults to current directory)."),
    remote_url: str = typer.Option(None, "--remote-url", "-r", help="Remote repository URL to link (sets git remote origin)."),
    venv_name: str = typer.Option(None, "--venv-name", "-n", help="Name of the virtual environment. If not provided, uses directory name."),
    backend: str = typer.Option(None, "--backend", "-b", help=f"Virtual environment backend ({'/'.join(SUPPORTED_BACKENDS)})."),
    python: str = typer.Option(None, "--python", "-p", help="Python version for the virtual environment."),
    package_manager: str = typer.Option(None, "--package-manager", "-m", help=f"Python package manager ({'/'.join(SUPPORTED_PACKAGE_MANAGERS)})."),
    base_deps: str = typer.Option(None, "--base-deps", "-d", help="Path to base dependencies file."),
    extra_deps: str = typer.Option(None, "--extra-deps", help="Extra dependency groups (e.g. 'dev,test')."),
    no_deps: bool = typer.Option(False, "--no-deps", is_flag=True, help="Skip dependency installation."),
    force: bool = typer.Option(False, "--force", "-f", is_flag=True, help="Overwrite existing environment without confirmation."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Show verbose output.")
) -> None:
    """
    Initialize a Git repository and create a virtual environment.

    Similar to `git init` but also sets up a virtual environment for the project.

    Any extra options will be passed directly to the `git init` command.

    Long options do not conflict between `gvit init` and `git init`.

    Short options might conflict; in that case, use the long form for the `git init` options.
    """
    # 1. Resolve and validate directory
    target_dir_ = Path(target_dir).resolve()
    validate_directory(target_dir_)

    # 2. Load local config
    local_config = load_local_config()
    verbose = verbose or get_verbose(local_config)

    # 3. Initialize git repository
    typer.echo(f'- Initializing Git repository in "{target_dir_}"...', nl=False)
    git = Git()
    git.init(str(target_dir_), ctx.args, verbose)

    # 4. Add remote if provided
    repo_url = ""
    if remote_url:
        typer.echo(f'\n- Adding remote origin "{remote_url}"...', nl=False)
        git.add_remote(str(target_dir_), remote_url, verbose)
        repo_url = remote_url

    # 5. Load repo config
    repo_config = load_repo_config(str(target_dir_))

    # 6. Create virtual environment
    backend = backend or get_backend(local_config)
    python = python or repo_config.get("gvit", {}).get("python") or get_python(local_config)
    package_manager = package_manager or get_package_manager(local_config)
    validate_backend(backend)
    validate_python(python)
    validate_package_manager(package_manager)
    registry_name, venv_name, venv_path = create_venv(venv_name, str(target_dir_), backend, python, force, verbose)

    # 7. Install dependencies
    if no_deps:
        resolved_base_deps = None
        resolved_extra_deps = {}
        typer.echo("\n- Skipping dependency installation...✅")
    else:
        resolved_base_deps, resolved_extra_deps = install_dependencies(
            venv_name=venv_name,
            backend=backend,
            package_manager=package_manager,
            repo_path=str(target_dir_),
            base_deps=base_deps,
            extra_deps=extra_deps,
            repo_config=repo_config,
            local_config=local_config,
            verbose=verbose
        )

    # 8. Save environment info to registry
    env_registry = EnvRegistry()
    env_registry.save_venv_info(
        registry_name=registry_name,
        venv_name=venv_name,
        venv_path=venv_path,
        repo_path=str(target_dir_),
        repo_url=repo_url,
        backend=backend,
        python=python,
        base_deps=resolved_base_deps,
        extra_deps=resolved_extra_deps
    )

    # 9. Summary message
    show_summary_message(
        registry_name=registry_name, repo_path=target_dir_, venv_path=Path(venv_path), backend=backend
    )
