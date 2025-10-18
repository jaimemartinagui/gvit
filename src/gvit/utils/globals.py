"""
Module with global variables.
"""

import os
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gvit"
CONFIG_FILE = CONFIG_DIR / "config.toml"

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

SUPPORTED_BACKENDS = [
    "venv",
    "virtualenv",
    "conda",
    "pyenv",
    "pipenv"
]
