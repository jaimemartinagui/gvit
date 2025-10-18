"""
Module with utility functions.
"""

import importlib.metadata
import pathlib

import toml


def get_version() -> str:
    """
    Get version from installed package metadata.
    If not installed (editable mode), read from pyproject.toml.
    """
    try:
        return importlib.metadata.version("gvit")
    except importlib.metadata.PackageNotFoundError:
        pyproject_path = pathlib.Path(__file__).parent.parent.parent / "pyproject.toml"
        if not pyproject_path.exists():
            raise RuntimeError("Could not determine gvit version.")
        version = toml.load(pyproject_path).get("project", {}).get("version")
        if not version:
            raise RuntimeError("Could not determine gvit version.")
        return version
