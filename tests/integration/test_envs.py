"""
Integration tests for envs commands.
"""

import toml
from typer.testing import CliRunner

from gvit.cli import app


runner = CliRunner()


class TestEnvsListCommand:
    """Test cases for 'gvit envs list' command."""

    def test_list_empty_registry(self, temp_config_dir):
        """Test listing environments when registry is empty."""
        result = runner.invoke(app, ["envs", "list"])
        assert result.exit_code == 0
        assert "No environments in registry" in result.output

    def test_list_with_environments(self, temp_config_dir, temp_repo):
        """Test listing environments with some registered."""
        envs_dir = temp_config_dir / "envs"
        
        # Create a sample environment
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(temp_repo / ".venv"),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(envs_dir / "test-env.toml", "w") as f:
            toml.dump(env_data, f)
        
        result = runner.invoke(app, ["envs", "list"])
        assert result.exit_code == 0
        assert "test-env" in result.output
        assert "venv" in result.output
        assert "3.11" in result.output


class TestEnvsDeleteCommand:
    """Test cases for 'gvit envs delete' command."""

    def test_delete_non_existent_environment(self, temp_config_dir):
        """Test deleting an environment that doesn't exist."""
        result = runner.invoke(app, ["envs", "delete", "non-existent", "-y"])
        # The command should complete but show a warning
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_delete_existing_environment(self, temp_config_dir, temp_repo, mocker):
        """Test deleting an existing environment."""
        envs_dir = temp_config_dir / "envs"
        
        # Create a venv directory
        venv_dir = temp_repo / ".venv"
        venv_dir.mkdir()
        
        # Create environment registry
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(venv_dir),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        env_file = envs_dir / "test-env.toml"
        with open(env_file, "w") as f:
            toml.dump(env_data, f)
        
        # Mock subprocess.run to avoid actual venv operations
        mock_run = mocker.patch("subprocess.run")
        
        result = runner.invoke(app, ["envs", "delete", "test-env", "-y"])
        assert result.exit_code == 0
        assert not env_file.exists()


class TestEnvsPruneCommand:
    """Test cases for 'gvit envs prune' command."""

    def test_prune_no_orphaned_envs(self, temp_config_dir, temp_repo):
        """Test prune when no orphaned environments exist."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment with existing repo
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(temp_repo / ".venv"),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(envs_dir / "test-env.toml", "w") as f:
            toml.dump(env_data, f)
        
        result = runner.invoke(app, ["envs", "prune"])
        assert result.exit_code == 0
        assert "no orphaned environments" in result.output.lower()

    def test_prune_with_orphaned_envs_dry_run(self, temp_config_dir):
        """Test prune with orphaned environments in dry-run mode."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment with non-existent repo
        env_data = {
            "environment": {
                "name": "orphaned-env",
                "backend": "venv",
                "python": "3.11",
                "path": "/tmp/non-existent/.venv",
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": "/tmp/non-existent",
                "url": "https://github.com/test/orphaned.git"
            }
        }
        
        env_file = envs_dir / "orphaned-env.toml"
        with open(env_file, "w") as f:
            toml.dump(env_data, f)
        
        result = runner.invoke(app, ["envs", "prune", "--dry-run"])
        assert result.exit_code == 0
        assert "orphaned-env" in result.output
        assert "DRY RUN" in result.output
        # File should still exist
        assert env_file.exists()

    def test_prune_with_orphaned_envs_yes_flag(self, temp_config_dir, mocker):
        """Test prune with orphaned environments using --yes flag."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment with non-existent repo
        env_data = {
            "environment": {
                "name": "orphaned-env",
                "backend": "venv",
                "python": "3.11",
                "path": "/tmp/non-existent/.venv",
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": "/tmp/non-existent",
                "url": "https://github.com/test/orphaned.git"
            }
        }
        
        env_file = envs_dir / "orphaned-env.toml"
        with open(env_file, "w") as f:
            toml.dump(env_data, f)
        
        # Mock subprocess to avoid actual deletion attempts
        mock_run = mocker.patch("subprocess.run")
        
        result = runner.invoke(app, ["envs", "prune", "--yes"])
        assert result.exit_code == 0
        assert "orphaned-env" in result.output


class TestEnvsShowActivateCommand:
    """Test cases for 'gvit envs show-activate' command."""

    def test_show_activate_no_environment(self, temp_config_dir, temp_repo, monkeypatch):
        """Test show-activate when no environment exists for current directory."""
        # Change to temp_repo directory
        monkeypatch.chdir(temp_repo)
        
        result = runner.invoke(app, ["envs", "show-activate"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "no tracked environment" in result.output.lower()

    def test_show_activate_venv_environment(self, temp_config_dir, temp_repo, monkeypatch):
        """Test show-activate for venv environment."""
        envs_dir = temp_config_dir / "envs"
        venv_path = temp_repo / ".venv"
        
        # Create environment registry
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(venv_path),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(envs_dir / "test-env.toml", "w") as f:
            toml.dump(env_data, f)
        
        # Change to temp_repo directory
        monkeypatch.chdir(temp_repo)
        
        result = runner.invoke(app, ["envs", "show-activate"])
        assert result.exit_code == 0
        assert "source" in result.output or "activate" in result.output

    def test_show_activate_by_name(self, temp_config_dir, temp_repo):
        """Test show-activate with specific environment name."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment registry
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(temp_repo / ".venv"),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(envs_dir / "test-env.toml", "w") as f:
            toml.dump(env_data, f)
        
        result = runner.invoke(app, ["envs", "show-activate", "--venv-name", "test-env"])
        assert result.exit_code == 0
        assert "source" in result.output or "activate" in result.output


class TestEnvsShowDeactivateCommand:
    """Test cases for 'gvit envs show-deactivate' command."""

    def test_show_deactivate_venv_environment(self, temp_config_dir, temp_repo, monkeypatch):
        """Test show-deactivate for venv environment."""
        envs_dir = temp_config_dir / "envs"
        
        # Create environment registry
        env_data = {
            "environment": {
                "name": "test-env",
                "backend": "venv",
                "python": "3.11",
                "path": str(temp_repo / ".venv"),
                "created_at": "2025-01-01T00:00:00.000000"
            },
            "repository": {
                "path": str(temp_repo),
                "url": "https://github.com/test/repo.git"
            }
        }
        
        with open(envs_dir / "test-env.toml", "w") as f:
            toml.dump(env_data, f)
        
        # Change to temp_repo directory
        monkeypatch.chdir(temp_repo)
        
        result = runner.invoke(app, ["envs", "show-deactivate"])
        assert result.exit_code == 0
        assert "deactivate" in result.output
