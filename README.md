
# 🧩 gvit

> **Automates virtual environment management for Git repositories.**

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

---

## ⚙️ What `gvit` does

* 🪄 **Automatically creates a virtual environment** when cloning a repo
* 📦 **Installs dependencies** from `requirements.txt`, `pyproject.toml`, or custom paths
* 🎯 **Supports extra dependencies** (dev, test, etc.) from `pyproject.toml` or separate files
* 🧠 **Remembers your preferences** via local configuration (`~/.config/gvit/config.toml`)
* ⚡ **Smart priority resolution**: CLI options → repo config → local config → defaults
* 🔧 **Flexible configuration**: per-repository (`.gvit.toml`) or global settings
* 🐍 **Conda backend support** (venv and virtualenv coming soon)

---

## 💻 Installation

> *The package is called `gvit` on PyPI, but the command is `gvit`.*

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
6. **Validates and handles conflicts**: 
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
│   ├── commands/
│   │   ├── clone.py        # Clone command logic
│   │   └── config.py       # Config management commands
│   ├── backends/
│   │   └── conda.py        # Conda backend implementation
│   ├── utils/
│   │   ├── utils.py        # Helper functions
│   │   ├── validators.py   # Input validation
│   │   ├── globals.py      # Constants and defaults
│   │   └── schemas.py      # Type definitions
│   └── __init__.py
└── pyproject.toml          # Project metadata
```

---

## 🧭 Roadmap

### Current Release (v0.0.2)

| Feature | Status | Description |
|---------|--------|-------------|
| **Clone command** | ✅ | Full repository cloning with environment setup |
| **Conda backend** | ✅ | Complete conda integration |
| **Config management** | ✅ | `setup`, `add-extra-deps`, `remove-extra-deps`, `show` |
| **Dependency resolution** | ✅ | Priority-based resolution (CLI > repo > local > default) |
| **pyproject.toml support** | ✅ | Install base + optional dependencies (extras) |
| **Requirements.txt support** | ✅ | Standard pip requirements files |
| **Custom dependency paths** | ✅ | Flexible path specification via config or CLI |
| **Environment validation** | ✅ | Detect conflicts, offer resolution options |

### Next Releases

| Version | Status | Description |
|---------|--------|-------------|
| **0.1.0** | 🔧 In Progress | Add `pull` and `checkout` commands with smart dependency sync |
| **0.2.0** | 📋 Planned | Support for `venv` and `virtualenv` backends |
| **0.3.0** | 📋 Planned | Environment persistence and metadata tracking |
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
gvit clone https://github.com/user/project.git \
  --venv-name custom-env \
  --python 3.12 \
  --backend conda \
  --base-deps requirements/prod.txt \
  --extra-deps dev:requirements/dev.txt,test:requirements/test.txt \
  --verbose
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
