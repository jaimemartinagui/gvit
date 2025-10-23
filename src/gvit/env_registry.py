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
from gvit.utils.schemas import EnvRegistryFile, EnvRegistryDeps


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

        env_info: EnvRegistryFile = {
            "environment": {
                "name": venv_name,
                "backend": backend,
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

            env_info["deps"] = cast(EnvRegistryDeps, deps_dict)

        with open(env_file, "w") as f:
            toml.dump(env_info, f)

        typer.echo("✅")

    # def get_dependencies_changed(self, venv_name: str) -> dict[str, bool]:
    #     """
    #     Check if dependency files have changed since installation.            
    #     Returns a dictionary mapping dependency names to whether they changed or not.
    #         Example: {"base": True, "dev": False}
    #     """
    #     env_info = self.load_environment_info(venv_name)
    #     if not env_info:
    #         return {}

    #     repo_path = Path(env_info["repository"]["path"])
    #     deps = env_info.get("deps", {})
    #     installed = deps.get("installed", {})

    #     changes = {}

    #     # Check base dependencies
    #     if "base" in deps and deps["base"]:
    #         base_file = repo_path / deps["base"]
    #         if base_file.exists():
    #             current_hash = self._hash_file(base_file)
    #             stored_hash = installed.get("base_hash", "")
    #             changes["base"] = current_hash != stored_hash

    #     # Check extra dependencies
    #     for key, path in deps.items():
    #         if key in ["base", "installed"]:
    #             continue
    #         dep_file = repo_path / path
    #         if dep_file.exists():
    #             current_hash = self._hash_file(dep_file)
    #             stored_hash = installed.get(f"{key}_hash", "")
    #             changes[key] = current_hash != stored_hash

    #     return changes

    def load_environment_info(self, venv_name: str) -> EnvRegistryFile | None:
        """Load environment information from registry."""
        env_file = ENVS_DIR / f"{venv_name}.toml"
        return cast(EnvRegistryFile, toml.load(env_file)) if env_file.exists() else None

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

    def get_orphaned_envs(self) -> list[EnvRegistryFile]:
        """Method to get environments if their repository path no longer exists."""
        to_prune = []
        for env_name in self.list_environments():
            env_info = self.load_environment_info(env_name)
            if not env_info:
                continue
            repo_path = Path(env_info['repository']['path'])
            if not repo_path.exists():
                to_prune.append(env_info)
        return to_prune

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
                deps_hashes["base_hash"] = self._hash_file(base_file)
        for name, path in extra_deps.items():
            dep_file = repo_abs_path / path
            if dep_file.exists():
                deps_hashes[f"{name}_hash"] = self._hash_file(dep_file)
        return deps_hashes

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file and return first 16 characters."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()[:16] if file_path.exists() else ""
