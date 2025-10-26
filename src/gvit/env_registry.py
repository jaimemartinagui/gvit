"""
Module for managing environment registry and persistence.
"""

from pathlib import Path
from datetime import datetime
import hashlib
from typing import cast, Any

import toml
import typer

from gvit.utils.globals import ENVS_DIR
from gvit.utils.schemas import RegistryFile, RegistryDeps


class EnvRegistry:
    """
    Class for managing environment registry and persistence.
    Stores information about created environments in ~/.config/gvit/envs/ folder.
    """

    def __init__(self) -> None:
        self._ensure_envs_dir()

    def save_environment_info(
        self,
        venv_name: str,
        venv_path: str,
        repo_path: str,
        repo_url: str,
        backend: str,
        python: str,
        base_deps: str | None,
        extra_deps: dict[str, str]
    ) -> None:
        """Save environment information to registry."""
        typer.echo("\n- Saving environment info to registry...", nl=False)
        env_file = ENVS_DIR / f"{venv_name}.toml"
        repo_abs_path = Path(repo_path).resolve()

        env_info: RegistryFile = {
            "environment": {
                "name": venv_name,
                "backend": backend,
                "path": venv_path,
                "python": python,
                "created_at": datetime.now().isoformat(),
            },
            "repository": {
                "path": str(repo_abs_path),
                "url": repo_url,
            }
        }

        if base_deps or extra_deps:
            deps_dict: dict[str, Any] = {
                **({"base": base_deps} if base_deps else {}),
                **extra_deps,
            }

            # Add installed info if we have hashes
            if deps_hashes := self._get_deps_hashes(base_deps, extra_deps, repo_abs_path):
                deps_dict["installed"] = {
                    **deps_hashes,
                    "installed_at": datetime.now().isoformat(),
                }

            env_info["deps"] = cast(RegistryDeps, deps_dict)

        with open(env_file, "w") as f:
            toml.dump(env_info, f)

        typer.echo("✅")

    def get_modified_deps_groups(self, venv_name: str, current_deps: dict[str, str]) -> list[str]:
        """
        Check if dependency files have changed since installation.            
        Returns a list of dependency group names that have changed.
        """
        env_info = self.load_environment_info(venv_name)
        if not env_info:
            return []

        deps = env_info.get("deps", {})
        installed = deps.get("installed", {})
        if not deps or not installed:
            return []

        repo_path = Path(env_info["repository"]["path"])
        modified_deps_groups = []

        for dep_name, dep_path in current_deps.items():
            installed_dep_name = f"{dep_name}_hash"
            if installed_dep_name not in installed:
                continue
            base_file = repo_path / dep_path
            if not base_file.exists():
                continue
            current_hash = (
                self._hash_pyproject_deps(base_file, None if dep_name == "base" else dep_name)
                if base_file.name == "pyproject.toml"
                else self._hash_file(base_file)
            )
            if current_hash != installed[installed_dep_name]:
                modified_deps_groups.append(dep_name)

        return modified_deps_groups

    def get_environments(self) -> list[RegistryFile]:
        """Method to get all the environments in the registry."""
        envs = [self.load_environment_info(env_name) for env_name in self.list_environments()]
        return [env for env in envs if env]

    def load_environment_info(self, venv_name: str) -> RegistryFile | None:
        """Load environment information from registry."""
        env_file = ENVS_DIR / f"{venv_name}.toml"
        return cast(RegistryFile, toml.load(env_file)) if env_file.exists() else None

    def list_environments(self) -> list[str]:
        """List all registered environments."""
        return sorted([f.stem for f in ENVS_DIR.glob("*.toml")]) if ENVS_DIR.exists() else []

    def environment_exists_in_registry(self, venv_name: str) -> bool:
        """Check if environment is registered."""
        env_file = ENVS_DIR / f"{venv_name}.toml"
        return env_file.exists()

    def delete_environment_registry(self, venv_name: str) -> bool:
        """
        Delete environment information from registry.
        Returns True if deleted, False if not found.
        """
        if (env_file := ENVS_DIR / f"{venv_name}.toml").exists():
            env_file.unlink()
            return True
        return False

    def get_orphaned_envs(self) -> list[RegistryFile]:
        """Method to get environments if their repository path no longer exists."""
        return [
            env for env in self.get_environments() if not Path(env['repository']['path']).exists()
        ]

    def _ensure_envs_dir(self) -> None:
        """Create environments directory if it does not exist."""
        ENVS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_deps_hashes(
        self, base_deps: str | None, extra_deps: dict[str, str], repo_abs_path: Path
    ) -> dict[str, str]:
        """Method to get the dictionary mapping the dependency group with its hash."""
        deps_hashes = {}
        if base_deps:
            base_file = repo_abs_path / base_deps
            if base_file.exists():
                hash_ = self._hash_pyproject_deps(base_file) if base_file.name == "pyproject.toml" else self._hash_file(base_file)
                if hash_:
                    deps_hashes["base_hash"] = hash_
        for name, path in extra_deps.items():
            dep_file = repo_abs_path / path
            if dep_file.exists():
                hash_ = self._hash_pyproject_deps(dep_file, name) if dep_file.name == "pyproject.toml" else self._hash_file(dep_file)
                if hash_:
                    deps_hashes[f"{name}_hash"] = hash_
        return deps_hashes

    def _hash_file(self, file_path: Path) -> str | None:
        """Calculate SHA256 hash of a file and return first 16 characters."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()[:16] if file_path.exists() else None

    def _hash_pyproject_deps(self, pyproject_path: Path, extra_dep: str | None = None) -> str | None:
        """
        Hash only a dependency section of pyproject.toml.
        If extra_dep is provided it hashes those deps [project.optional-dependencies.<extra_dep>].
        If no extra_dep is provided it hashes the base deps [project.dependencies].
        """
        if not pyproject_path.exists():
            return None
        try:
            content = toml.load(pyproject_path)
            deps = (
                content.get("project", {}).get("optional-dependencies", {}).get(extra_dep)
                if extra_dep else content.get("project", {}).get("dependencies")
            )
            return hashlib.sha256(str(sorted(deps)).encode()).hexdigest()[:16] if deps else None
        except Exception:
            return None
