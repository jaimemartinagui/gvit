"""
Module with global variables.
"""

import os
from pathlib import Path


LOCAL_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gvit"
LOCAL_CONFIG_FILE = LOCAL_CONFIG_DIR / "config.toml"
ENVS_DIR = LOCAL_CONFIG_DIR / "envs"
LOGS_DIR = LOCAL_CONFIG_DIR / "logs"
LOG_FILE = LOGS_DIR / "commands.csv"
REPO_CONFIG_FILE = ".gvit.toml"
FAKE_SLEEP_TIME = 0.75
MIN_PYTHON_VERSION = "3.10"

DEFAULT_BACKEND = "venv"
DEFAULT_VENV_NAME = ".venv"
DEFAULT_PYTHON = "3.11"
DEFAULT_PACKAGE_MANAGER = "uv"
DEFAULT_BASE_DEPS = "requirements.txt"
DEFAULT_VERBOSE = False
DEFAULT_LOG_ENABLED = True
DEFAULT_LOG_MAX_ENTRIES = 1_000
DEFAULT_LOG_SHOW_LIMIT = 50
DEFAULT_LOG_IGNORED_COMMANDS = [
    "config.add-extra-deps",
    "config.remove-extra-deps",
    "config.show",
    "envs.list",
    "envs.show",
    "envs.show-activate",
    "envs.show-deactivate",
    "logs.show",
    "logs.stats",
    "status",
    "tree"
]

SUPPORTED_BACKENDS = [
    "venv",
    "conda",
    "virtualenv",
    "uv"
]

SUPPORTED_PACKAGE_MANAGERS = [
    "uv",
    "pip"
]

ASCII_LOGO = r"""
                      ░██   ░██    
                            ░██    
 ░████████ ░██    ░██ ░██░████████ 
░██    ░██ ░██    ░██ ░██   ░██    
░██    ░██  ░██  ░██  ░██   ░██    
░██   ░███   ░██░██   ░██   ░██    
 ░█████░██    ░███    ░██    ░████ 
       ░██                         
 ░███████                          


Git-aware Virtual Environment Manager
"""
