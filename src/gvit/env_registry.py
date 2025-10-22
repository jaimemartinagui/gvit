"""
Module for managing environment registry and persistence.
"""

from pathlib import Path
from datetime import datetime
import hashlib

import toml

from gvit.utils.globals import ENVS_DIR


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
        env_file = ENVS_DIR / f"{venv_name}.toml"
        repo_abs_path = Path(repo_path).resolve()

        # Calculate hashes of dependency files for change detection
        deps_hashes = {}
        if base_deps:
            base_file = repo_abs_path / base_deps
            if base_file.exists():
                deps_hashes["base_hash"] = self._hash_file(base_file)

        for name, path in extra_deps.items():
            dep_file = repo_abs_path / path
            if dep_file.exists():
                deps_hashes[f"{name}_hash"] = self._hash_file(dep_file)

        # Build environment info structure
        env_info = {
            "environment": {
                "name": venv_name,
                "backend": backend,
                "python": python,
                "created_at": datetime.now().isoformat(),
            },
            "repository": {
                "path": str(repo_abs_path),
                "url": repo_url,
            },
            "deps": {
                **({"base": base_deps} if base_deps else {}),
                **extra_deps,
            }
        }

        # Add installed info if we have hashes
        if deps_hashes:
            env_info["deps"]["installed"] = {
                **deps_hashes,
                "installed_at": datetime.now().isoformat(),
            }

        with open(env_file, "w") as f:
            toml.dump(env_info, f)


    def get_dependencies_changed(self, venv_name: str) -> dict[str, bool]:
        """
        Check if dependency files have changed since installation.            
        Returns a dictionary mapping dependency names to whether they changed or not.
            Example: {"base": True, "dev": False}
        """
        env_info = self.load_environment_info(venv_name)
        if not env_info:
            return {}

        repo_path = Path(env_info["repository"]["path"])
        deps = env_info.get("deps", {})
        installed = deps.get("installed", {})

        changes = {}

        # Check base dependencies
        if "base" in deps and deps["base"]:
            base_file = repo_path / deps["base"]
            if base_file.exists():
                current_hash = self._hash_file(base_file)
                stored_hash = installed.get("base_hash", "")
                changes["base"] = current_hash != stored_hash

        # Check extra dependencies
        for key, path in deps.items():
            if key in ["base", "installed"]:
                continue
            dep_file = repo_path / path
            if dep_file.exists():
                current_hash = self._hash_file(dep_file)
                stored_hash = installed.get(f"{key}_hash", "")
                changes[key] = current_hash != stored_hash

        return changes

    def load_environment_info(self, venv_name: str) -> dict | None:
        """Load environment information from registry."""
        env_file = ENVS_DIR / f"{venv_name}.toml"
        return toml.load(env_file) if env_file.exists() else None

    def list_environments(self) -> list[str]:
        """List all registered environments."""
        return sorted([f.stem for f in ENVS_DIR.glob("*.toml")]) if ENVS_DIR.exists() else []

    def environment_exists_in_registry(self, venv_name: str) -> bool:
        """Check if environment is registered."""
        env_file = ENVS_DIR / f"{venv_name}.toml"
        return env_file.exists()

    def delete_environment_from_registry(self, venv_name: str) -> bool:
        """
        Delete environment information from registry.
        Returns True if deleted, False if not found.
        """
        env_file = ENVS_DIR / f"{venv_name}.toml"
        if not env_file.exists():
            return False
        env_file.unlink()
        return True

    def _ensure_envs_dir(self) -> None:
        """Create environments directory if it does not exist."""
        ENVS_DIR.mkdir(parents=True, exist_ok=True)

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file and return first 16 characters."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()[:16] if file_path.exists() else ""
