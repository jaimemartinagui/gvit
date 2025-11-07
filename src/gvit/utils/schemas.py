"""
Module with the schemas.
"""

from typing import TypedDict, NotRequired


# ==================== Local Config schemas ====================

class CondaConfig(TypedDict):
    path: str


class VenvConfig(TypedDict):
    name: str


class VirtualenvConfig(TypedDict):
    name: str


class GvitLocalConfig(TypedDict):
    backend: NotRequired[str]
    python: NotRequired[str]
    package_manager: NotRequired[str]
    verbose: NotRequired[bool]


class DepsLocalConfig(TypedDict):
    _base: NotRequired[str]
    # Additional dependency groups can be any string key


class BackendsConfig(TypedDict):
    conda: NotRequired[CondaConfig]
    venv: NotRequired[VenvConfig]
    virtualenv: NotRequired[VirtualenvConfig]
    uv: NotRequired[VirtualenvConfig]


class LoggingConfig(TypedDict):
    enabled: NotRequired[bool]
    max_entries: NotRequired[int]
    ignored: NotRequired[list[str]]


class LocalConfig(TypedDict):
    """Schema for the local configuration of gvit (~/.config/gvit/config.toml)."""
    gvit: NotRequired[GvitLocalConfig]
    deps: NotRequired[DepsLocalConfig]
    backends: NotRequired[BackendsConfig]
    logging: NotRequired[LoggingConfig]

# ==============================================================


# ===================== Repo Config schemas ====================

class GvitRepoConfig(TypedDict):
    python: NotRequired[str]


class DepsRepoConfig(TypedDict):
    _base: NotRequired[str]
    # Additional dependency groups can be any string key


class RepoConfig(TypedDict):
    """Schema for the repository configuration of gvit (.gvit.toml or pyproject.toml)."""
    gvit: NotRequired[GvitRepoConfig]
    deps: NotRequired[DepsRepoConfig]

# ==============================================================


# ====================== Regsitry schemas ======================

class RegistryEnvironment(TypedDict):
    name: str
    backend: str
    path: str
    python: str
    created_at: str  # ISO format datetime string


class RegistryRepository(TypedDict):
    path: str  # Absolute path to repository
    url: str


class RegistryDepsInstalled(TypedDict):
    _base_hash: str | None  # SHA256 hash (first 16 chars)
    _freeze_hash: str | None  # SHA256 hash (first 16 chars) of pip freeze output
    _freeze: str | None  # Complete pip freeze output
    installed_at: str  # ISO format datetime string
    # Additional hashes for extra deps: {dep_name}_hash


class RegistryDeps(TypedDict):
    _base: NotRequired[str]  # Path to base dependencies file
    installed: NotRequired[RegistryDepsInstalled]
    # Additional dependency groups can be any string key


class RegistryFile(TypedDict):
    """Schema for environment registry file (~/.config/gvit/envs/{venv_name}.toml)."""
    environment: RegistryEnvironment
    repository: RegistryRepository
    deps: NotRequired[RegistryDeps]

# ==============================================================
