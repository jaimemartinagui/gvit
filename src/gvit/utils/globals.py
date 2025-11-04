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

DEFAULT_BACKEND = "venv"
DEFAULT_VENV_NAME = ".venv"
DEFAULT_PYTHON = "3.11"
DEFAULT_BASE_DEPS = "requirements.txt"
DEFAULT_VERBOSE = False
DEFAULT_LOG_ENABLED = True
DEFAULT_MAX_LOG_ENTRIES = 1000
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
    # "pyenv",
    # "pipenv"
]

SUPPORTED_PYTHONS = [
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
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
