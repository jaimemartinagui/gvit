"""
Module with global variables.
"""

import os
from pathlib import Path


LOCAL_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gvit"
LOCAL_CONFIG_FILE = LOCAL_CONFIG_DIR / "config.toml"
REPO_CONFIG_FILE = ".gvit.toml"

DEFAULT_BACKEND = "conda"
DEFAULT_PYTHON = "3.11"
DEFAULT_ACTIVATE = True
DEFAULT_INSTALL_DEPS = True
DEFAULT_DEPS_PATH = "requirements.txt"
DEFAULT_VERBOSE = False

SUPPORTED_BACKENDS = [
    # "venv",
    # "virtualenv",
    "conda",
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
