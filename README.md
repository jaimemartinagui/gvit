
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

<div>

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/gvit.svg)](https://pypi.org/project/gvit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-49%20passing-brightgreen.svg)](#-testing)
[![Coverage](https://img.shields.io/badge/coverage-33%25-orange.svg)](#-testing)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 📋 Table of Contents

- ⭐ [Vision](#-vision)
- 🚀 [Motivation](#-motivation)
- ☑️ [What gvit does](#️-what-gvit-does)
- 💻 [Installation](#-installation)
- 🧩 [Usage](#-usage)
  - [Initial Configuration](#initial-configuration)
  - [Clone a Repository](#clone-a-repository)
  - [Initialize a New Project](#initialize-a-new-project)
  - [Setup an Existing Repository](#setup-an-existing-repository)
  - [Pull Changes](#pull-changes-and-update-dependencies)
  - [Commit with Validation](#commit-with-dependency-validation)
  - [Check Status](#check-status)
  - [Configuration Management](#configuration-management)
  - [Environment Management](#environment-management)
  - [Git Commands](#use-git-commands-directly)
  - [Explore Commands](#explore-commands)
- 🧠 [How it works](#-how-it-works)
- ⚙️ [Configuration](#️-configuration)
- 🧱 [Architecture](#-architecture)
- 🧭 [Roadmap](#-roadmap)
- 🧪 [Testing](#-testing)
- 🤝 [Contributing](#-contributing)
- ⚖️ [License](#️-license)

---

## ⭐ Vision

> *“One repo, its own environment — without thinking about it.”*

The goal of **`gvit`** CLI is to eliminate the need to manually create or update virtual environments. No more friction between version control and Python environment management. Git and Python should work together seamlessly — this tool makes it possible.

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
# Clone from scratch
gvit clone https://github.com/someone/project.git

# Or setup an existing repo
cd existing-project
gvit setup
```

🎉 Environment created and dependencies installed!

### When to use gvit vs other tools

**Use `gvit` if you:**
- Work on multiple projects simultaneously.
- Want Git workflows to automatically sync environments.
- Need centralized environment tracking.
- Want flexibility in backends (e.g. `conda` is crucial for certain DS/ML projects).
- Work with legacy projects that still do not use `pyproject.toml`.

**Use `uv` if you:**
- Primarily work on one project at a time.
- Want the fastest package installation.
- Focus on modern Python packaging (`pyproject.toml`).
- Need advanced dependency resolution.

---

## ☑️ What `gvit` does

* 🪄 **Automatically creates environments** when cloning or initializing repos.
* 📦 **Installs dependencies** from `requirements.txt`, `pyproject.toml`, or custom paths.
* 🎯 **Supports extra dependencies** (dev, test, etc.) from `pyproject.toml` or separate files.
* 🔄 **Git command fallback**: Use `gvit` for all git commands - unknown commands automatically fallback to git.
* 🧠 **Remembers your preferences** via local configuration (`~/.config/gvit/config.toml`).
* 📝 **Tracks environments** in registry (`~/.config/gvit/envs/`) with metadata and dependency hashes.
* 🧘 **Cleans orphaned environments** automatically with `prune` command.
* 🌳 **Visual command tree** to explore available commands.
* 🔧 **Flexible configuration**: per-repository (`.gvit.toml`) or global settings.
* 🐍 **Multiple backends**: `venv` (built-in), `conda`, and `virtualenv` support.
* 🔒 **Dependency validation**: `commit` command validates installed packages match declared dependencies.
* 📄 **Status overview**: `status` command shows both Git and environment changes in one view.

---

## 💻 Installation

⚠️ **Important:** Install `gvit` **globally**, not in a project-specific virtual environment. Since `gvit` manages virtual environments, it needs to be available system-wide.

### Recommended: pipx (isolated global install)

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install gvit with pipx
pipx install gvit
```

**Why pipx?**
- ✅ Installs CLI tools in isolated environments
- ✅ Makes them globally available
- ✅ Prevents dependency conflicts
- ✅ Easy to upgrade and uninstall

### Alternative: pip (global install)

```bash
# Install globally (may require sudo on some systems)
pip install gvit

# Or with --user flag
pip install --user gvit
```

### Verify Installation

```bash
gvit --version

# Should work from any directory
cd ~ && gvit --version
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
gvit config setup --backend venv --python 3.11 --base-deps requirements.txt

# or use conda
gvit config setup --backend conda --python 3.12

# or use virtualenv
gvit config setup --backend virtualenv --python 3.11
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

<img src="assets/img/clone.png" alt="gvit clone example" width="400">

### Initialize a New Project

Similar to `git init` but with environment setup:

```bash
# In current directory
gvit init

# In specific directory (--target-dir)
gvit init -t my-project

# With remote repository
gvit init --remote-url https://github.com/user/my-project.git

# With all options
gvit init -t my-project \
  --remote-url https://github.com/user/my-project.git \
  --python 3.12 \
  --extra-deps dev,test
```

### Setup an Existing Repository

If you already have a cloned repository and want to set up the environment:

```bash
# In the repository directory
cd my-existing-repo
gvit setup

# Or specify a different directory (--target-dir)
gvit setup -t path/to/repo

# With custom options
gvit setup --python 3.12 --extra-deps dev,test

# Skip dependency installation
gvit setup --no-deps
```

### Pull Changes and Update Dependencies

Smart `git pull` that automatically detects and reinstalls changed dependencies:

```bash
# Pull and auto-update dependencies if changed
gvit pull

# Pull without checking dependencies
gvit pull --no-deps

# Force reinstall all dependencies even if unchanged
gvit pull --force-deps

# Pass options to git pull
gvit pull --rebase origin main
```

### Commit with Dependency Validation

Smart `git commit` that validates your installed packages match your dependency files:

```bash
# Commit with automatic validation
gvit commit -m "Add new feature"

# Skip validation if needed
gvit commit --skip-validation -m "Quick fix"

# Pass any git commit options
gvit commit -a -m "Update everything"
gvit commit --amend
```

**What it validates:**
- ✅ Detects added packages not declared in dependency files.
- ✅ Detects removed packages still declared in dependency files.
- ✅ Detects version changes not reflected in pinned versions.
- ✅ Works with `requirements.txt`, `pyproject.toml`, and custom paths.
- ✅ Shows detailed diff of package changes (added/removed/modified).

### Check Status

Combined view of Git status and environment changes:

```
# Show just repository (same as `git status`)
gvit status

# Show repository and environment status
gvit status -e

# In a specific directory
gvit status -e --target-dir path/to/repo
```

**What it shows:**
- 📂 **Repository Status**: Standard `git status` output.
- 🐍 **Environment Status**: Packages added/removed/modified since last tracking.
- ✅ Clean overview of both code and dependency changes.
- ⚡ Quick way to see if you need to update dependency files.

<img src="assets/img/status.png" alt="gvit status example" width="400">

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

# Reset an environment (recreate and reinstall dependencies)
gvit envs reset my-env

# Reset without reinstalling dependencies
gvit envs reset my-env --no-deps

# Show activate command for current repository's environment
gvit envs show-activate

# Show activate command for a specific environment
gvit envs show-activate --venv-name my-env

# Show activate command with relative path (venv/virtualenv only)
gvit envs show-activate --relative

# Activate environment directly (recommended)
eval "$(gvit envs show-activate)"

# Show deactivate command for current repository's environment
gvit envs show-deactivate

# Show deactivate command for a specific environment
gvit envs show-deactivate --venv-name my-env

# Deactivate environment directly (recommended)
eval "$(gvit envs show-deactivate)"

# Clean up orphaned environments (repos that no longer exist)
gvit envs prune

# Preview what would be removed
gvit envs prune --dry-run

# Auto-confirm removal
gvit envs prune --yes
```

<img src="assets/img/prune.png" alt="gvit prune example" width="400">

### Use Git Commands Directly

`gvit` can replace `git` in your daily workflow! Any command not implemented in `gvit` automatically falls back to `git`:

```bash
# These work exactly like git commands
gvit add file.py
gvit diff --stat
gvit log --oneline -10
gvit branch -a
gvit checkout -b feature
gvit push origin main
gvit stash
gvit rebase main

# Complete workflow with gvit
gvit status              # gvit's enhanced status
gvit add .
gvit commit -m "feat"    # gvit's validated commit
gvit push
```

**How it works:**
- 🔍 `gvit` checks if the command is implemented (clone, commit, init, pull, status, etc.).
- ✅ If implemented: runs `gvit`'s enhanced version.
- 🔄 If not implemented: automatically forwards to `git`.
- 🎯 Seamless experience - just replace `git` with `gvit`.

**Git aliases support:**

`gvit` automatically resolves your **git aliases** and uses `gvit`'s enhanced versions when available!

```bash
# If you have git aliases configured:
# git config --global alias.st status
# git config --global alias.ci commit
# git config --global alias.co checkout

# These will use gvit's enhanced versions
gvit st -e   # → gvit status (with environment tracking)
gvit ci -m   # → gvit commit (with validation)

# This will use git directly
gvit co main # → git checkout main
```

- 🔗 Respects all your existing git aliases.
- 🚀 Automatically uses `gvit`'s enhanced versions when the alias resolves to a gvit command.
- 🔄 Falls back to git for other commands.

### Explore Commands

```bash
# Show all available commands in tree structure
gvit tree

# Output
gvit
├── clone
├── commit
├── config
│   ├── add-extra-deps
│   ├── remove-extra-deps
│   ├── setup
│   └── show
├── envs
│   ├── delete
│   ├── list
│   ├── prune
│   ├── reset
│   ├── show
│   ├── show-activate
│   └── show-deactivate
├── init
├── pull
├── setup
├── status
└── tree
```

---

## 🧠 How it works

### Git related commands

**`gvit clone`** → Clones repository + creates environment:
1. **Clones the repository** using standard `git clone`.
2. **Detects repository name** from URL (handles `.git` suffix correctly).
3. Proceeds to environment setup.

**`gvit init`** → Initializes Git repository + creates environment:
1. **Initializes Git repository** using `git init`.
2. **Optionally adds remote** if `--remote-url` is provided.
3. Proceeds to environment setup.

**`gvit setup`** → Creates environment for existing repository:
1. **Verifies Git repository** exists in target directory.
2. **Detects remote URL** if available.
3. Proceeds to environment setup.

**`gvit pull`** → Pulls changes and syncs dependencies:
1. **Finds tracked environment** for current repository.
2. **Runs `git pull`** with any extra arguments you provide.
3. **Compares dependency file hashes** (stored in registry vs. current files).
4. **Reinstalls only changed dependencies** automatically.
5. **Updates registry** with new hashes.

**`gvit commit`** → Validates dependencies before committing:
1. **Finds tracked environment** for current repository.
2. **Compares pip freeze outputs** (stored snapshot vs. current state).
3. **Detects package changes**: added, removed, modified versions.
4. **Validates dependency files** to ensure changes are reflected.
5. **Shows detailed report** of discrepancies (if any).
6. **Runs `git commit`** with any extra arguments you provide.

**`gvit status`** → Shows combined repository and environment status:
1. **Displays `git status` output** for repository changes.
2. **Finds tracked environment** for current repository.
3. **Compares pip freeze outputs** (stored snapshot vs. current state).
4. **Shows package changes**: added, removed, modified versions.
5. **Provides clean overview** of both code and dependency changes.

### Environment Setup Process (common to all commands)

1. **Creates virtual environment** using your preferred backend:
   - **`venv`**: Python's built-in venv module (creates `.venv/`, or the defined environment name, in repo).
   - **`virtualenv`**: Enhanced virtual environments (creates `.venv/`, or the defined environment name, in repo).
   - **`conda`**: Conda environments (centralized management).
2. **Resolves dependencies** with priority system:
   - CLI arguments (highest priority).
   - Repository config (`.gvit.toml`).
   - Local config (`~/.config/gvit/config.toml`).
   - Default values (lowest priority).
3. **Installs dependencies** from:
   - `pyproject.toml` (with optional extras support).
   - `requirements.txt` or custom paths.
   - Multiple dependency groups (_base, dev, test, etc.).
4. **Tracks environment in registry**:
   - Saves environment metadata to `~/.config/gvit/envs/{env_name}.toml`.
   - Records dependency file hashes for change detection.
   - Stores complete pip freeze snapshot for validation.
   - Stores repository information (path, URL).
5. **Validates and handles conflicts**: 
   - Detects existing environments.
   - Offers options: rename, overwrite, or abort.
   - Auto-generates unique names if needed.

---

## ⚙️ Configuration

### Local Configuration

Global preferences: `~/.config/gvit/config.toml`

```toml
[gvit]
backend = "venv"  # or "conda", "virtualenv"
python = "3.11"

[deps]
_base = "requirements.txt"
dev = "requirements-dev.txt"
test = "requirements-test.txt"

[backends.venv]
name = ".venv"  # Directory name for venv (default: .venv)

[backends.virtualenv]
name = ".venv"  # Directory name for virtualenv (default: .venv)

[backends.conda]
path = "/path/to/conda"  # Optional: custom conda path
```

### Environment Registry

Environment tracking: `~/.config/gvit/envs/{env_name}.toml`

```toml
[environment]
name = "my-project"
backend = "conda"
path = "/Users/user/miniconda3/envs/gvit"
python = "3.11"
created_at = "2025-01-22T20:53:01.123456"

[repository]
path = "/Users/user/projects/my-project"
url = "https://github.com/user/my-project.git"

[deps]
_base = "requirements.txt"
dev = "requirements-dev.txt"

[deps.installed]
_base_hash = "a1b2c3d4e5f6g7h8"  # SHA256 hash for change detection
dev_hash = "i9j0k1l2m3n4o5p6"
_freeze_hash = "q7r8s9t0u1v2w3x4"  # SHA256 hash of pip freeze output
_freeze = """  # Complete pip freeze snapshot for validation
package1==1.0.0
package2==2.3.4
"""
installed_at = "2025-01-22T20:53:15.789012"
```

### Repository Configuration

Per-project settings: `.gvit.toml` (in repository root)

```toml
[gvit]
python = "3.12"  # Override Python version for this project

[deps]
_base = "requirements.txt"
dev = "requirements-dev.txt"
internal = "requirements-internal.txt"
```

Or use `pyproject.toml` (tool section):

```toml
[tool.gvit]
python = "3.12"

[tool.gvit.deps]
_base = "pyproject.toml"
```

---

## 🧱 Architecture

### Project Structure

```
gvit/
├── src/gvit/                       # Source code
│   ├── cli.py                      # CLI entry point & command routing
│   ├── env_registry.py             # Environment registry management
│   ├── git.py                      # Git operations & alias resolution
│   ├── commands/                   # Command implementations
│   │   ├── clone.py                # Clone repos with auto environment setup
│   │   ├── init.py                 # Initialize new Git repos + environments
│   │   ├── setup.py                # Setup environments for existing repos
│   │   ├── pull.py                 # Smart pull with dependency sync
│   │   ├── commit.py               # Commit with dependency validation
│   │   ├── status.py               # Git + environment status overview
│   │   ├── tree.py                 # Visual command structure explorer
│   │   ├── config.py               # Configuration management
│   │   └── envs.py                 # Environment management (list, delete, etc)
│   ├── backends/                   # Backend implementations
│   │   ├── common.py               # Shared backend functions
│   │   ├── venv.py                 # Python's built-in venv
│   │   ├── virtualenv.py           # virtualenv (faster, more features)
│   │   └── conda.py                # conda environments
│   └── utils/                      # Utilities & helpers
│       ├── exceptions.py           # Custom exception classes
│       ├── globals.py              # Constants and defaults
│       ├── schemas.py              # Type definitions (TypedDict)
│       ├── utils.py                # Helper functions
│       └── validators.py           # Input validation
├── tests/                          # Test suite (49 tests, 33% coverage)
│   ├── unit/                       # Unit tests (38 tests)
│   │   ├── test_env_registry.py
│   │   ├── test_backends/
│   │   └── test_utils/
│   ├── integration/                # Integration tests (11 tests)
│   │   └── test_envs.py
│   ├── fixtures/                   # Test fixtures
│   ├── conftest.py                 # Shared pytest fixtures
│   └── README.md                   # Complete testing guide
├── .coveragerc                     # Coverage configuration
├── pytest.ini                      # Pytest configuration
├── pyproject.toml                  # Project metadata & dependencies
└── README.md                       # This file
```

### Key Components

#### Core Modules

- **`cli.py`** - Entry point with Typer app, command routing, and git fallback.
- **`env_registry.py`** - Manages environment tracking in `~/.config/gvit/envs/`.
- **`git.py`** - Git operations, alias resolution, and git command execution.

#### Commands Layer

Each command is self-contained with its own logic:

#### Backends Layer

Abstraction for different virtual environment tools.

#### Utils Layer

Support utilities (configuration paths, defaults, constants, custom exceptions, etc.).

### Data Flow

```
1. User runs command
   ↓
2. cli.py parses with Typer
   ↓
3. Command module executes logic
   ↓
4. Backend creates/manages environment
   ↓
5. env_registry.py tracks metadata
   ↓
6. Files saved to ~/.config/gvit/
```

### Configuration Hierarchy

```
CLI Arguments (highest priority)
  ↓
Repository Config (.gvit.toml or pyproject.toml)
  ↓
Local Config (~/.config/gvit/config.toml)
  ↓
Defaults (globals.py)
```

---

## 🧭 Roadmap

### Current Release (v0.4.0)

| Feature | Status | Description |
|---------|--------|-------------|
| **Clone command** | ✅ | Full repository cloning with environment setup |
| **Init command** | ✅ | Initialize new Git repos with environment setup |
| **Setup command** | ✅ | Create environment for existing repositories |
| **Pull command** | ✅ | Smart git pull with automatic dependency sync |
| **Commit command** | ✅ | Git commit with automatic dependency validation |
| **Tree command** | ✅ | Visual command structure explorer |
| **Venv backend** | ✅ | Python's built-in venv support |
| **Conda backend** | ✅ | Complete conda integration |
| **Virtualenv backend** | ✅ | Complete virtualenv integration |
| **Config management** | ✅ | `setup`, `add-extra-deps`, `remove-extra-deps`, `show` |
| **Environment registry** | ✅ | Track environments with metadata, dependency hashes, and freeze snapshots |
| **Environment management** | ✅ | `list`, `show`, `delete`, `prune`, `reset`, `show-activate`, `show-deactivate` commands |
| **Orphan cleanup** | ✅ | Automatic detection and removal of orphaned environments |
| **Dependency resolution** | ✅ | Priority-based resolution (CLI > repo > local > default) |
| **pyproject.toml support** | ✅ | Install base + optional dependencies (extras) |
| **Requirements.txt support** | ✅ | Standard pip requirements files |
| **Custom dependency paths** | ✅ | Flexible path specification via config or CLI |
| **Environment validation** | ✅ | Detect conflicts, offer resolution options |
| **TypedDict schemas** | ✅ | Full type safety with typed configuration schemas |
| **Dependency validation** | ✅ | Validate installed packages match declared dependencies on commit |
| **Status command** | ✅ | Combined view of Git status and environment changes |
| **Git command fallback** | ✅ | Automatic fallback to git for unknown commands |

### Next Releases

| Version | Status | Description |
|---------|--------|-------------|
| **0.6.0** | 📋 Planned | Add `checkout` command to switch branches and sync deps |
| **0.6.0** | 📋 Planned | `gvit sync` command for full dependency refresh |
| **1.0.0** | 🎯 Goal | Stable release with all core features |

---

## 🧪 Testing

`gvit` has a comprehensive test suite with 49 tests and growing coverage.

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage report
pytest --cov=src/gvit --cov-report=html
open tests/htmlcov/index.html
```

**Test Suite:**
- ✅ 38 unit tests (fast, isolated)
- ✅ 11 integration tests (end-to-end)
- ✅ 33% coverage (target: 80%+)
- ✅ Fully isolated (no system side effects)

**Documentation:** See [tests/README.md](tests/README.md) for the complete testing guide including:
- How to run and write tests.
- Coverage analysis.
- Available fixtures.
- Best practices.

---

## 🤝 Contributing

Contributions are welcome! Areas we'd love help with:

- Additional backends (pyenv, poetry).
- `checkout` and other commands.
- Cross-platform testing.
- Documentation improvements.
- **Writing tests** - See [tests/README.md](tests/README.md)

Open an issue or submit a pull request on [GitHub](https://github.com/jaimemartinagui/gvit).

---

## ⚖️ License

MIT © 2025
