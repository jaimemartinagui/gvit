"""
Unit tests for EnvRegistry class.
"""

import toml

from gvit.env_registry import EnvRegistry


class TestEnvRegistry:
    """Test cases for EnvRegistry class."""

    def test_init_creates_envs_dir(self, temp_config_dir):
        """Test that EnvRegistry creates envs directory on init."""
        envs_dir = temp_config_dir / "envs"
        # Directory is created by isolate_tests fixture
        assert envs_dir.exists()
        
        registry = EnvRegistry()
        assert envs_dir.exists()

    def test_list_environments_empty(self, env_registry):
        """Test listing environments when registry is empty."""
        envs = env_registry.list_environments()
        assert envs == []

    def test_list_environments_with_entries(self, env_registry, temp_config_dir):
        """Test listing environments with some registered environments."""
        envs_dir = temp_config_dir / "envs"
        
        # Create some dummy environment files
        (envs_dir / "env1.toml").touch()
        (envs_dir / "env2.toml").touch()
        (envs_dir / "env3.toml").touch()
        
        envs = env_registry.list_environments()
        assert len(envs) == 3
        assert "env1" in envs
        assert "env2" in envs
        assert "env3" in envs
        # Should be sorted
        assert envs == ["env1", "env2", "env3"]

    def test_venv_exists_in_registry(self, env_registry, temp_config_dir):
        """Test checking if environment exists in registry."""
        envs_dir = temp_config_dir / "envs"
        
        assert not env_registry.venv_exists_in_registry("test-env")
        
        (envs_dir / "test-env.toml").touch()
        assert env_registry.venv_exists_in_registry("test-env")

    def test_save_venv_info_basic(self, env_registry, temp_config_dir, temp_repo):
        """Test saving basic environment information."""
        envs_dir = temp_config_dir / "envs"
        
        env_registry.save_venv_info(
            registry_name="test-env",
            venv_name="test-env",
            venv_path=str(temp_repo / ".venv"),
            repo_path=str(temp_repo),
            repo_url="https://github.com/test/repo.git",
            backend="venv",
            python="3.11",
            base_deps=None,
            extra_deps={},
            created_at="2025-01-01T00:00:00.000000"
        )
        
        env_file = envs_dir / "test-env.toml"
        assert env_file.exists()
        
        data = toml.load(env_file)
        assert data["environment"]["name"] == "test-env"
        assert data["environment"]["backend"] == "venv"
        assert data["environment"]["python"] == "3.11"
        assert data["repository"]["url"] == "https://github.com/test/repo.git"

    def test_save_venv_info_with_deps(self, env_registry, temp_config_dir, temp_repo):
        """Test saving environment information with dependencies."""
        # Create a requirements file
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests==2.31.0\nclick==8.1.0\n")
        
        envs_dir = temp_config_dir / "envs"
        
        env_registry.save_venv_info(
            registry_name="test-env",
            venv_name="test-env",
            venv_path=str(temp_repo / ".venv"),
            repo_path=str(temp_repo),
            repo_url="https://github.com/test/repo.git",
            backend="venv",
            python="3.11",
            base_deps="requirements.txt",
            extra_deps={},
            created_at="2025-01-01T00:00:00.000000"
        )
        
        env_file = envs_dir / "test-env.toml"
        data = toml.load(env_file)
        
        assert "deps" in data
        assert data["deps"]["_base"] == "requirements.txt"
        assert "installed" in data["deps"]
        assert "_base_hash" in data["deps"]["installed"]

    def test_load_environment_info(self, env_registry, temp_config_dir):
        """Test loading environment information."""
        envs_dir = temp_config_dir / "envs"
        env_file = envs_dir / "test-env.toml"
        
        # Create a sample environment file
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": "/tmp/test/.venv",
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": "/tmp/test",
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(env_file, "w") as f:
            toml.dump(env_data, f)
        
        loaded_info = env_registry.load_environment_info("test-env")
        assert loaded_info is not None
        assert loaded_info["environment"]["name"] == "test-env"
        assert loaded_info["environment"]["backend"] == "venv"

    def test_load_environment_info_not_found(self, env_registry):
        """Test loading non-existent environment."""
        loaded_info = env_registry.load_environment_info("non-existent")
        assert loaded_info is None

    def test_delete_environment_registry(self, env_registry, temp_config_dir):
        """Test deleting environment from registry."""
        envs_dir = temp_config_dir / "envs"
        env_file = envs_dir / "test-env.toml"
        env_file.touch()
        
        assert env_file.exists()
        result = env_registry.delete_environment_registry("test-env")
        assert result is True
        assert not env_file.exists()

    def test_delete_environment_registry_not_found(self, env_registry):
        """Test deleting non-existent environment."""
        result = env_registry.delete_environment_registry("non-existent")
        assert result is False

    def test_get_environments(self, env_registry, temp_config_dir):
        """Test getting all environments."""
        envs_dir = temp_config_dir / "envs"
        
        # Create multiple environment files
        for i in range(3):
            env_file = envs_dir / f"env{i}.toml"
            env_data = {
                "environment": {
                    "name": f"env{i}",
                    "backend": "venv",
                    "python": "3.11",
                    "path": f"/tmp/env{i}/.venv",
                    "created_at": "2025-01-01T00:00:00.000000"
                },
                "repository": {
                    "path": f"/tmp/env{i}",
                    "url": f"https://github.com/test/env{i}.git"
                }
            }
            with open(env_file, "w") as f:
                toml.dump(env_data, f)
        
        envs = env_registry.get_environments()
        assert len(envs) == 3
        assert all(isinstance(env, dict) for env in envs)

    def test_get_orphaned_envs(self, env_registry, temp_config_dir, temp_repo):
        """Test getting orphaned environments."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment with existing repo path
        env1_file = envs_dir / "env1.toml"
        env1_data = {
            "environment": {
                "name": "env1",
                "backend": "venv",
                "python": "3.11",
                "path": str(temp_repo / ".venv"),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/env1.git"
            }
        }
        with open(env1_file, "w") as f:
            toml.dump(env1_data, f)
        
        # Create environment with non-existent repo path
        env2_file = envs_dir / "env2.toml"
        env2_data = {
            "environment": {
                "name": "env2",
                "backend": "venv",
                "python": "3.11",
                "path": "/tmp/non-existent/.venv",
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": "/tmp/non-existent",
                "url": "https://github.com/test/env2.git"
            }
        }
        with open(env2_file, "w") as f:
            toml.dump(env2_data, f)
        
        orphaned = env_registry.get_orphaned_envs()
        assert len(orphaned) == 1
        assert orphaned[0]["environment"]["name"] == "env2"

    def test_hash_file(self, env_registry, temp_repo):
        """Test file hashing."""
        test_file = temp_repo / "test.txt"
        test_file.write_text("test content")
        
        hash1 = env_registry._hash_file(test_file)
        assert hash1 is not None
        assert len(hash1) == 16  # First 16 chars of SHA256
        
        # Same content should produce same hash
        hash2 = env_registry._hash_file(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash3 = env_registry._hash_file(test_file)
        assert hash1 != hash3

    def test_hash_file_not_exists(self, env_registry, temp_repo):
        """Test hashing non-existent file."""
        non_existent = temp_repo / "non-existent.txt"
        hash_result = env_registry._hash_file(non_existent)
        assert hash_result is None
