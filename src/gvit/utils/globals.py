"""
Module with global variables.
"""

import os
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gvit"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_BACKEND = "venv"
DEFAULT_PYTHON = "3.11"
DEFAULT_INSTALL_DEPS = True
DEFAULT_ACTIVATE = True
DEFAULT_VERBOSE = False

SUPPORTED_BACKENDS = [
    "venv",
    "virtualenv",
    "conda",
    "pyenv",
    "pipenv"
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
