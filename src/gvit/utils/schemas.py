"""
Module with the schemas.
"""

from typing import TypedDict, NotRequired


class CondaConfig(TypedDict):
    path: str


class VenvConfig(TypedDict):
    name: str


class BackendsConfig(TypedDict):
    conda: NotRequired[CondaConfig]
    venv: NotRequired[VenvConfig]


class GvitLocalConfig(TypedDict):
    backend: NotRequired[str]
    python: NotRequired[str]
    verbose: NotRequired[bool]


class GvitRepoConfig(TypedDict):
    python: NotRequired[str]


class DepsLocalConfig(TypedDict):
    base: NotRequired[str]
    # Additional dependency groups can be any string key


class DepsRepoConfig(TypedDict):
    base: NotRequired[str]
    # Additional dependency groups can be any string key


class LocalConfig(TypedDict):
    """Schema for the local configuration of gvit (~/.config/gvit/config.toml)."""
    gvit: NotRequired[GvitLocalConfig]
    deps: NotRequired[DepsLocalConfig]
    backends: NotRequired[BackendsConfig]


class RepoConfig(TypedDict):
    """Schema for the repository configuration of gvit (.gvit.toml or pyproject.toml)."""
    gvit: NotRequired[GvitRepoConfig]
    deps: NotRequired[DepsRepoConfig]


class EnvRegistryEnvironment(TypedDict):
    """Schema for environment section in registry file."""
    name: str
    backend: str
    path: str
    python: str
    created_at: str  # ISO format datetime string


class EnvRegistryRepository(TypedDict):
    """Schema for repository section in registry file."""
    path: str  # Absolute path to repository
    url: str


class EnvRegistryDepsInstalled(TypedDict):
    """Schema for installed deps tracking in registry file."""
    base_hash: NotRequired[str]  # SHA256 hash (first 16 chars)
    installed_at: str  # ISO format datetime string
    # Additional hashes for extra deps: {dep_name}_hash


class EnvRegistryDeps(TypedDict):
    """Schema for deps section in registry file."""
    base: NotRequired[str]  # Path to base dependencies file
    installed: NotRequired[EnvRegistryDepsInstalled]
    # Additional dependency groups can be any string key


class EnvRegistryFile(TypedDict):
    """Schema for environment registry file (~/.config/gvit/envs/{venv_name}.toml)."""
    environment: EnvRegistryEnvironment
    repository: EnvRegistryRepository
    deps: NotRequired[EnvRegistryDeps]
