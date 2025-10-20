"""
Module with the schemas.
"""

from typing import TypedDict


class CondaConfig(TypedDict, total=False):
    path: str


class BackendsConfig(TypedDict, total=False):
    conda: CondaConfig


class DefaultsConfig(TypedDict, total=False):
    backend: str
    python: str
    install_deps: bool
    deps_path: str


class GvitRepoConfig(TypedDict, total=False):
    python: str
    deps_path: str


class LocalConfig(TypedDict, total=False):
    """Schema for the local configuration of gvit (~/.config/gvit/config.toml)."""
    defaults: DefaultsConfig
    backends: BackendsConfig


class RepoConfig(TypedDict, total=False):
    """Schema for the repository configuration of gvit (.gvit.toml or pyproject.toml)."""
    gvit: GvitRepoConfig
