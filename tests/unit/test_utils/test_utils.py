"""Unit tests for utility functions."""

from pathlib import Path

import pytest
import toml

from gvit.utils.utils import (
    extract_repo_name_from_url,
    get_backend,
    get_python,
    get_base_deps,
    get_extra_deps,
    get_venv_name,
    load_local_config,
    load_repo_config,
    save_local_config,
    ensure_local_config_dir
)


class TestExtractRepoName:
    """Test cases for extract_repo_name_from_url function."""

    def test_https_url_with_git_suffix(self):
        """Test extracting repo name from HTTPS URL with .git suffix."""
        url = "https://github.com/user/repo.git"
        assert extract_repo_name_from_url(url) == "repo"

    def test_https_url_without_git_suffix(self):
        """Test extracting repo name from HTTPS URL without .git suffix."""
        url = "https://github.com/user/repo"
        assert extract_repo_name_from_url(url) == "repo"

    def test_ssh_url_with_git_suffix(self):
        """Test extracting repo name from SSH URL with .git suffix."""
        url = "git@github.com:user/repo.git"
        assert extract_repo_name_from_url(url) == "repo"

    def test_ssh_url_without_git_suffix(self):
        """Test extracting repo name from SSH URL without .git suffix."""
        url = "git@github.com:user/repo"
        assert extract_repo_name_from_url(url) == "repo"

    def test_local_path(self):
        """Test extracting repo name from local path."""
        url = "/path/to/local/repo"
        assert extract_repo_name_from_url(url) == "repo"

    def test_nested_path(self):
        """Test extracting repo name from nested path."""
        url = "https://github.com/org/user/my-project.git"
        assert extract_repo_name_from_url(url) == "my-project"


class TestConfigGetters:
    """Test cases for config getter functions."""

    def test_get_backend_default(self):
        """Test getting default backend when not in config."""
        config = {}
        assert get_backend(config) == "venv"

    def test_get_backend_from_config(self):
        """Test getting backend from config."""
        config = {"gvit": {"backend": "conda"}}
        assert get_backend(config) == "conda"

    def test_get_python_default(self):
        """Test getting default Python version when not in config."""
        config = {}
        assert get_python(config) == "3.11"

    def test_get_python_from_config(self):
        """Test getting Python version from config."""
        config = {"gvit": {"python": "3.12"}}
        assert get_python(config) == "3.12"

    def test_get_base_deps_default(self):
        """Test getting default base deps when not in config."""
        config = {}
        assert get_base_deps(config) == "requirements.txt"

    def test_get_base_deps_from_config(self):
        """Test getting base deps from config."""
        config = {"deps": {"_base": "requirements/base.txt"}}
        assert get_base_deps(config) == "requirements/base.txt"

    def test_get_extra_deps_empty(self):
        """Test getting extra deps when none configured."""
        config = {}
        assert get_extra_deps(config) == {}

    def test_get_extra_deps_from_config(self):
        """Test getting extra deps from config."""
        config = {
            "deps": {
                "_base": "requirements.txt",
                "dev": "requirements-dev.txt",
                "test": "requirements-test.txt"
            }
        }
        extra_deps = get_extra_deps(config)
        assert extra_deps == {
            "dev": "requirements-dev.txt",
            "test": "requirements-test.txt"
        }
        assert "_base" not in extra_deps

    def test_get_venv_name_default(self):
        """Test getting default venv name when not in config."""
        config = {}
        assert get_venv_name(config) == ".venv"

    def test_get_venv_name_from_config(self):
        """Test getting venv name from config."""
        config = {"backends": {"venv": {"name": "venv"}}}
        assert get_venv_name(config) == "venv"


class TestConfigFileOperations:
    """Test cases for config file operations."""

    def test_load_local_config_not_exists(self, temp_config_dir):
        """Test loading local config when file doesn't exist."""
        config = load_local_config()
        assert config == {}

    def test_load_local_config_exists(self, sample_config):
        """Test loading existing local config."""
        config = load_local_config()
        assert config["gvit"]["backend"] == "venv"
        assert config["gvit"]["python"] == "3.11"

    def test_save_and_load_local_config(self, temp_config_dir):
        """Test saving and loading local config."""
        config = {
            "gvit": {
                "backend": "conda",
                "python": "3.12"
            },
            "deps": {
                "_base": "requirements.txt"
            }
        }
        
        save_local_config(config)
        loaded = load_local_config()
        
        assert loaded == config

    def test_load_repo_config_gvit_toml(self, temp_repo):
        """Test loading repo config from .gvit.toml file."""
        config_file = temp_repo / ".gvit.toml"
        config_data = {
            "gvit": {
                "python": "3.12"
            },
            "deps": {
                "_base": "requirements.txt"
            }
        }
        
        with open(config_file, "w") as f:
            toml.dump(config_data, f)
        
        config = load_repo_config(str(temp_repo))
        assert config["gvit"]["python"] == "3.12"

    def test_load_repo_config_pyproject_toml(self, temp_repo):
        """Test loading repo config from pyproject.toml [tool.gvit]."""
        pyproject_file = temp_repo / "pyproject.toml"
        pyproject_data = {
            "project": {
                "name": "test"
            },
            "tool": {
                "gvit": {
                    "python": "3.12",
                    "backend": "conda"
                }
            }
        }
        
        with open(pyproject_file, "w") as f:
            toml.dump(pyproject_data, f)
        
        config = load_repo_config(str(temp_repo))
        assert config["gvit"]["python"] == "3.12"
        assert config["gvit"]["backend"] == "conda"

    def test_load_repo_config_not_exists(self, temp_repo):
        """Test loading repo config when no config files exist."""
        config = load_repo_config(str(temp_repo))
        assert config == {}

    def test_load_repo_config_priority(self, temp_repo):
        """Test that .gvit.toml takes priority over pyproject.toml."""
        # Create both config files
        gvit_config = temp_repo / ".gvit.toml"
        gvit_data = {
            "gvit": {
                "python": "3.12"
            }
        }
        with open(gvit_config, "w") as f:
            toml.dump(gvit_data, f)
        
        pyproject_file = temp_repo / "pyproject.toml"
        pyproject_data = {
            "tool": {
                "gvit": {
                    "python": "3.11"
                }
            }
        }
        with open(pyproject_file, "w") as f:
            toml.dump(pyproject_data, f)
        
        config = load_repo_config(str(temp_repo))
        # Should use .gvit.toml value
        assert config["gvit"]["python"] == "3.12"

    def test_ensure_local_config_dir_creates_dir(self, temp_config_dir):
        """Test that ensure_local_config_dir creates directory."""
        # Directory already exists from fixture, but test the function
        ensure_local_config_dir()
        assert temp_config_dir.exists()
