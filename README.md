
```
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
```

**Automates virtual environment management for Git repositories.**

`gvit` is a command-line tool that automatically creates and manages virtual environments when you clone repositories. Its goal is to eliminate friction between **version control** and **Python environment management**.

---

## 🚀 Motivation

Have you ever cloned a project and had to do all this?

```bash
git clone https://github.com/someone/project.git
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

With **`gvit`**, all of that happens automatically:

```bash
gvit clone https://github.com/someone/project.git
```

🎉 Repository cloned, environment created, and dependencies installed!

### Examples

![gvit clone example](assets/img/clone.png)

![gvit prune example](assets/img/prune.png)

---

## ⚙️ What `gvit` does

* 🪄 **Automatically creates environments** when cloning or initializing repos
* 📦 **Installs dependencies** from `requirements.txt`, `pyproject.toml`, or custom paths
* 🎯 **Supports extra dependencies** (dev, test, etc.) from `pyproject.toml` or separate files
* 🧠 **Remembers your preferences** via local configuration (`~/.config/gvit/config.toml`)
* 📝 **Tracks environments** in registry (`~/.config/gvit/envs/`) with metadata and dependency hashes
* 🧼 **Cleans orphaned environments** automatically with `prune` command
* 🌳 **Visual command tree** to explore available commands
* ⚡ **Smart priority resolution**: CLI options → repo config → local config → defaults
* 🔧 **Flexible configuration**: per-repository (`.gvit.toml`) or global settings
* 🐍 **Conda backend support** (venv and virtualenv coming soon)

---

## 💻 Installation

```bash
pip install gvit
```

Or with `pipx` (recommended for CLI tools):

```bash
pipx install gvit
```

---

## 🧩 Usage

### Initial Configuration

Set up your default preferences (interactive):

```bash
gvit config setup
```

Or specify options directly:

```bash
gvit config setup --backend conda --python 3.11 --base-deps requirements.txt
```

### Clone a Repository

Basic clone with automatic environment creation:

```bash
gvit clone https://github.com/user/repo.git
```

**Advanced options:**

```bash
# Custom environment name
gvit clone https://github.com/user/repo.git --venv-name my-env

# Specify Python version
gvit clone https://github.com/user/repo.git --python 3.12

# Install extra dependencies from pyproject.toml
gvit clone https://github.com/user/repo.git --extra-deps dev,test

# Skip dependency installation
gvit clone https://github.com/user/repo.git --no-deps

# Force overwrite existing environment
gvit clone https://github.com/user/repo.git --force

# Verbose output
gvit clone https://github.com/user/repo.git --verbose
```

### Initialize a New Project

Similar to `git init` but with environment setup:

```bash
# In current directory
gvit init

# In specific directory
gvit init my-project

# With remote repository
gvit init --remote-url https://github.com/user/my-project.git

# With all options
gvit init my-project \
  --remote-url https://github.com/user/my-project.git \
  --python 3.12 \
  --extra-deps dev,test
```

### Configuration Management

```bash
# Add extra dependency groups to local config
gvit config add-extra-deps dev requirements-dev.txt
gvit config add-extra-deps test requirements-test.txt

# Remove extra dependency groups
gvit config remove-extra-deps dev

# Show current configuration
gvit config show
```

### Environment Management

```bash
# List all tracked environments
gvit envs list

# Show details of a specific environment
gvit envs show my-env

# Remove an environment (registry and backend)
gvit envs delete my-env

# Clean up orphaned environments (repos that no longer exist)
gvit envs prune

# Preview what would be removed
gvit envs prune --dry-run

# Auto-confirm removal
gvit envs prune --yes
```

### Explore Commands

```bash
# Show all available commands in tree structure
gvit tree
```

---

## 🧠 How it works

1. **Clones the repository** using standard `git clone`
2. **Detects repository name** from URL (handles `.git` suffix correctly)
3. **Creates virtual environment** using your preferred backend:
   - Currently: `conda`
   - Coming soon: `venv`, `virtualenv`
4. **Resolves dependencies** with priority system:
   - CLI arguments (highest priority)
   - Repository config (`.gvit.toml`)
   - Local config (`~/.config/gvit/config.toml`)
   - Default values (lowest priority)
5. **Installs dependencies** from:
   - `pyproject.toml` (with optional extras support)
   - `requirements.txt` or custom paths
   - Multiple dependency groups (base, dev, test, etc.)
6. **Tracks environment in registry**:
   - Saves environment metadata to `~/.config/gvit/envs/{env_name}.toml`
   - Records dependency file hashes for change detection
   - Stores repository information (path, URL)
7. **Validates and handles conflicts**: 
   - Detects existing environments
   - Offers options: rename, overwrite, or abort
   - Auto-generates unique names if needed

---

## ⚙️ Configuration

### Local Configuration

Global preferences: `~/.config/gvit/config.toml`

```toml
[gvit]
backend = "conda"
python = "3.11"

[deps]
base = "requirements.txt"
dev = "requirements-dev.txt"
test = "requirements-test.txt"

[backends.conda]
path = "/path/to/conda"  # Optional: custom conda path
```

### Environment Registry

Environment tracking: `~/.config/gvit/envs/{env_name}.toml`

```toml
[environment]
name = "my-project"
backend = "conda"
python = "3.11"
created_at = "2025-01-22T20:53:01.123456"

[repository]
path = "/Users/user/projects/my-project"
url = "https://github.com/user/my-project.git"

[deps]
base = "requirements.txt"
dev = "requirements-dev.txt"

[deps.installed]
base_hash = "a1b2c3d4e5f6g7h8"  # SHA256 hash for change detection
dev_hash = "i9j0k1l2m3n4o5p6"
installed_at = "2025-01-22T20:53:15.789012"
```

### Repository Configuration

Per-project settings: `.gvit.toml` (in repository root)

```toml
[gvit]
python = "3.12"  # Override Python version for this project

[deps]
base = "requirements.txt"
dev = "requirements-dev.txt"
internal = "requirements-internal.txt"
```

Or use `pyproject.toml` (tool section):

```toml
[tool.gvit]
python = "3.12"

[tool.gvit.deps]
base = "pyproject.toml"
```

---

## 🧱 Architecture

```
gvit/
├── src/gvit/
│   ├── cli.py              # CLI entry point (Typer app)
│   ├── env_registry.py     # Environment registry management
│   ├── commands/
│   │   ├── _common.py      # Shared functions between commands
│   │   ├── clone.py        # Clone command logic
│   │   ├── init.py         # Init command logic
│   │   ├── tree.py         # Tree command (show command structure)
│   │   ├── config.py       # Config management commands
│   │   └── envs.py         # Environment management commands
│   ├── backends/
│   │   └── conda.py        # Conda backend implementation
│   ├── utils/
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── utils.py        # Helper functions
│   │   ├── validators.py   # Input validation
│   │   ├── globals.py      # Constants and defaults
│   │   └── schemas.py      # Type definitions (TypedDict)
│   └── __init__.py
└── pyproject.toml          # Project metadata
```

---

## 🧭 Roadmap

### Current Release (v0.0.3)

| Feature | Status | Description |
|---------|--------|-------------|
| **Clone command** | ✅ | Full repository cloning with environment setup |
| **Init command** | ✅ | Initialize new Git repos with environment setup |
| **Tree command** | ✅ | Visual command structure explorer |
| **Conda backend** | ✅ | Complete conda integration |
| **Config management** | ✅ | `setup`, `add-extra-deps`, `remove-extra-deps`, `show` |
| **Environment registry** | ✅ | Track environments with metadata and dependency hashes |
| **Environment management** | ✅ | `list`, `show`, `delete`, `prune` commands |
| **Orphan cleanup** | ✅ | Automatic detection and removal of orphaned environments |
| **Dependency resolution** | ✅ | Priority-based resolution (CLI > repo > local > default) |
| **pyproject.toml support** | ✅ | Install base + optional dependencies (extras) |
| **Requirements.txt support** | ✅ | Standard pip requirements files |
| **Custom dependency paths** | ✅ | Flexible path specification via config or CLI |
| **Environment validation** | ✅ | Detect conflicts, offer resolution options |
| **TypedDict schemas** | ✅ | Full type safety with typed configuration schemas |

### Next Releases

| Version | Status | Description |
|---------|--------|-------------|
| **0.1.0** | 🔧 In Progress | Add `pull` command with smart dependency sync using registry |
| **0.2.0** | 📋 Planned | Add `checkout` command to switch branches and sync deps |
| **0.3.0** | 📋 Planned | Support for `venv` and `virtualenv` backends |
| **0.4.0** | 📋 Planned | Shell integration and aliases |
| **1.0.0** | 🎯 Goal | Stable release with all core features |

---

## 🧑‍💻 Example Workflows

### First Time Setup

```bash
# Install gvit
pipx install gvit

# Configure defaults
gvit config setup --backend conda --python 3.11

# Add common dependency groups
gvit config add-extra-deps dev requirements-dev.txt
gvit config add-extra-deps test requirements-test.txt
```

### Standard Project

```bash
# Clone with base dependencies
gvit clone https://github.com/user/project.git

# Activate environment
conda activate project
```

### Project with Extra Dependencies

```bash
# Clone and install dev dependencies
gvit clone https://github.com/user/project.git --extra-deps dev

# Or multiple groups
gvit clone https://github.com/user/project.git --extra-deps dev,test

# Activate
conda activate project
```

### Project with pyproject.toml

```bash
# Install base dependencies from pyproject.toml
gvit clone https://github.com/user/project.git

# Install with optional dependencies defined in [project.optional-dependencies]
gvit clone https://github.com/user/project.git --extra-deps dev,test
```

### Custom Configuration

```bash
# Override everything from CLI
gvit clone https://github.com/user/project.git \\
  --venv-name custom-env \\
  --python 3.12 \\
  --backend conda \\
  --base-deps requirements/prod.txt \\
  --extra-deps dev:requirements/dev.txt,test:requirements/test.txt \\
  --verbose
```

### Initialize a New Project

```bash
# Create a new project from scratch
mkdir my-new-project
cd my-new-project
gvit init --remote-url https://github.com/user/my-new-project.git

# Now ready to work
echo "# My Project" > README.md
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Managing Tracked Environments

```bash
# See all environments gvit knows about
gvit envs list

# Check environment details (shows registry file with syntax highlighting)
gvit envs show my-project

# Remove specific environment (registry + conda env)
gvit envs delete old-project

# Clean up all orphaned environments
gvit envs prune

# See what would be cleaned without actually removing
gvit envs prune --dry-run
```

### Explore Available Commands

```bash
# Show command tree
gvit tree

# Output:
# gvit
# ├── clone
# ├── init
# ├── config/
# │   ├── setup
# │   ├── add-extra-deps
# │   ├── remove-extra-deps
# │   └── show
# ├── envs/
# │   ├── list
# │   ├── show
# │   ├── delete
# │   └── prune
# └── tree
```

---

## 🤝 Contributing

Contributions are welcome! Areas we'd love help with:

- Additional backends (venv, virtualenv, pyenv)
- `pull` and `checkout` commands
- Cross-platform testing
- Documentation improvements

Open an issue or submit a pull request on [GitHub](https://github.com/jaimemartinagui/gvit).

---

## ⚖️ License

MIT © 2025

---

## ⭐ Vision

> *“One repo, its own environment — without thinking about it.”*

The goal of **`gvit`** is to eliminate the need to manually create or update virtual environments. Git and Python should work together seamlessly — this tool makes it possible.
