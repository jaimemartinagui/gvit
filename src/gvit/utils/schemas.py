"""
Module with the schemas.
"""

from typing import TypedDict


class CondaConfig(TypedDict, total=False):
    path: str


class BackendsConfig(TypedDict, total=False):
    conda: CondaConfig


class GvitLocalConfig(TypedDict, total=False):
    backend: str
    python: str
    verbose: bool


class GvitRepoConfig(TypedDict, total=False):
    python: str


class DepsLocalConfig(TypedDict, total=False):
    install: bool
    base: str
    # Additional dependency groups can be any string key


class DepsRepoConfig(TypedDict, total=False):
    base: str
    # Additional dependency groups can be any string key


class LocalConfig(TypedDict, total=False):
    """Schema for the local configuration of gvit (~/.config/gvit/config.toml)."""
    gvit: GvitLocalConfig
    deps: DepsLocalConfig
    backends: BackendsConfig


class RepoConfig(TypedDict, total=False):
    """Schema for the repository configuration of gvit (.gvit.toml or pyproject.toml)."""
    gvit: GvitRepoConfig
    deps: DepsRepoConfig
