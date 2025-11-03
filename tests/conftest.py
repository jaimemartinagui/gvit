"""Shared pytest fixtures for all tests."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import toml

from gvit.env_registry import EnvRegistry
from gvit.utils.globals import LOCAL_CONFIG_DIR, ENVS_DIR


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    
    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    
    return repo_path


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch) -> Path:
    """Create a temporary config directory and patch globals."""
    # Note: isolate_tests already creates these directories
    # This fixture just returns the path that was created
    config_dir = tmp_path / "config" / "gvit"
    
    # Ensure directories exist (may already be created by isolate_tests)
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "envs").mkdir(exist_ok=True)
    
    return config_dir


@pytest.fixture
def sample_config(temp_config_dir: Path) -> Path:
    """Create a sample gvit config file."""
    config_file = temp_config_dir / "config.toml"
    config_data = {
        "gvit": {
            "backend": "venv",
            "python": "3.11"
        },
        "deps": {
            "_base": "requirements.txt"
        },
        "backends": {
            "venv": {
                "name": ".venv"
            }
        }
    }
    
    with open(config_file, "w") as f:
        toml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def sample_requirements(temp_repo: Path) -> Path:
    """Create a sample requirements.txt file."""
    req_file = temp_repo / "requirements.txt"
    req_file.write_text("requests==2.31.0\nclick==8.1.0\n")
    return req_file


@pytest.fixture
def env_registry(temp_config_dir: Path) -> EnvRegistry:
    """Provide an EnvRegistry instance with temp config."""
    return EnvRegistry()


@pytest.fixture
def mock_venv_creation(mocker):
    """Mock virtual environment creation."""
    return mocker.patch("subprocess.run")


@pytest.fixture
def sample_env_info() -> dict:
    """Provide sample environment information."""
    return {
        "environment": {
            "name": "test-env",
            "backend": "venv",
            "python": "3.11",
            "path": "/tmp/test-repo/.venv",
            "created_at": "2025-01-01T00:00:00.000000"
        },
        "repository": {
            "path": "/tmp/test-repo",
            "url": "https://github.com/test/test-repo.git"
        },
        "deps": {
            "_base": "requirements.txt"
        },
        "deps.installed": {
            "_base_hash": "abc123",
            "_freeze_hash": "def456",
            "_freeze": "requests==2.31.0\\nclick==8.1.0\\n",
            "installed_at": "2025-01-01T00:00:00.000000"
        }
    }


@pytest.fixture(autouse=True)
def isolate_tests(monkeypatch, tmp_path):
    """Isolate each test by using temporary directories for config."""
    # Create isolated temp directories
    temp_config = tmp_path / "config" / "gvit"
    temp_envs = temp_config / "envs"
    temp_config.mkdir(parents=True)
    temp_envs.mkdir()
    
    # Patch all references to config directories and files
    config_file = temp_config / "config.toml"
    monkeypatch.setattr("gvit.utils.globals.LOCAL_CONFIG_DIR", temp_config)
    monkeypatch.setattr("gvit.utils.globals.LOCAL_CONFIG_FILE", config_file)
    monkeypatch.setattr("gvit.utils.globals.ENVS_DIR", temp_envs)
    # Also patch in the utils module since it imports at module level
    monkeypatch.setattr("gvit.utils.utils.LOCAL_CONFIG_FILE", config_file)
    monkeypatch.setattr("gvit.utils.utils.LOCAL_CONFIG_DIR", temp_config)
    monkeypatch.setattr("gvit.env_registry.ENVS_DIR", temp_envs)
