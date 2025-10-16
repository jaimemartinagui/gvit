
# 🧩 gvit

> **Automates virtual environment management for Git repositories.**

`gvit` is a command-line tool that automatically creates and synchronizes a virtual environment whenever you clone or update a repository. Its goal is to eliminate friction between **version control** and **Python environment management**.

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

With **`gvit`**, all of that disappears. When you clone, you'll already have a ready-to-use virtual environment configured with the repo dependencies.

```bash
gvit clone https://github.com/someone/project.git
```

🎉 And you are ready to work!

---

## ⚙️ What `gvit` does

* 🪄 **Automatically creates a virtual environment** when cloning a repo.
* 🔄 **Synchronizes dependencies** when running `gvit pull` (if `pyproject.toml`, `requirements.txt`, etc. have changed).
* 🧠 **Remembers your preferred backend** (`venv`, `virtualenv`, `conda`, `pyenv`, etc.).
* 🪶 **Does not interfere with Git**: it just enhances the workflow.
* 🧰 **Optionally generates aliases** to integrate commands with Git.

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

## 🧩 Basic Usage

### 🌀 Clone a repo and create its environment

```bash
gvit clone https://github.com/yourorg/my-project.git
```

Automatically creates a virtual environment named after the repository (e.g., `.venv-my-project`) and initializes it with dependencies.

---

### 🔄 Synchronize dependencies when updating

```bash
gvit pull
```

Runs `git pull` and, if dependencies have changed, updates the environment.

---

### ⚙️ Configure automatic aliases

```bash
gvit create-aliases
```

Creates a `git()` function in your shell (Bash or Zsh) that intercepts only relevant commands:

```bash
git clone ...  →  gvit clone ...
git pull  ...  →  gvit pull ...
```

Does not affect `git commit`, `push`, or other commands.

To revert the aliases:

```bash
gvit remove-aliases
```

---

## 🧠 How it works internally

1. Detects the **repository name** from the URL or local folder.
2. Uses your preferred backend (configurable) to create the environment:

   * `venv` (default)
   * `virtualenv`
   * `conda`
   * `pyenv`
3. Associates the environment with the repo via a small `.gvit` metadata file.
4. On each `pull`, checks if dependency files (`requirements.txt`, `pyproject.toml`, `environment.yml`, etc.) have changed.
5. If they have, **automatically updates the environment**.

---

## ⚙️ Local Configuration

Preferences can be set in a global configuration file:

`~/.config/gvit/config.toml`

Example:

```toml
[settings]
backend = "conda"
auto_update = true
default_env_dir = ".venv"
```

---

## 🧱 Architecture (in development)

```
git_venv/
├── cli.py          # CLI entry point
├── backends/       # Integrations with venv, conda, pyenv, etc.
├── git_utils.py    # Functions for clone, pull, etc.
├── env_manager.py  # Core logic for creation and synchronization
└── shell_utils.py  # Automatic alias/function creation
```

---

## 🧭 Roadmap

| Version   | Status                                           | Description |
| --------- | ------------------------------------------------ | ----------- |
| **0.0.1** | ✅ Initial publication on PyPI (name reservation) |             |
| **0.1.0** | 🔧 Minimal CLI (`clone`, `pull`, `--help`)       |             |
| **0.2.0** | 🧰 Support for `conda`, `virtualenv`, `pyenv`    |             |
| **0.3.0** | 🪄 Automatic alias system                        |             |
| **0.4.0** | ⚙️ Global and local configuration                |             |
| **0.5.0** | 🚀 Smart detection of dependency changes         |             |
| **1.0.0** | 🎉 Stable release                                |             |

---

## 🧑‍💻 Example workflow

```bash
# Set preferred backend
gvit config --backend conda

# Clone project and create environment
gvit clone https://github.com/example/project.git

# Activate the environment
source .venv-project/bin/activate

# Sync after repo update
gvit pull
```

---

## ⚖️ License

MIT © 2025 — [Your Name](https://github.com/yourusername)

---

## 💬 Contributing

Contributions are welcome! Open an issue or submit a pull request on [GitHub](https://github.com/yourusername/gvit).

---

## ⭐ Vision

> *“One repo, its own environment — without thinking about it.”*

The goal of **`gvit`** is to eliminate the need to manually create or update virtual environments. Git and Python should work together seamlessly — this tool makes it possible.
