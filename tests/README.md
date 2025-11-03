# Testing Guide for `gvit`

Comprehensive guide for testing `gvit` - from quick start to advanced coverage analysis.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📁 Test Structure](#-test-structure)
- [🏃 Running Tests](#-running-tests)
- [✍️ Writing Tests](#-writing-tests)
- [📊 Coverage](#-coverage)
- [🔧 Fixtures](#-fixtures)
- [✅ Best Practices](#-best-practices)
- [🐛 Troubleshooting](#-troubleshooting)
- [🎯 Next Steps](#-next-steps)
- [📚 Resources](#-resources)
- [📈 Current Status](#-current-status)

---

## 🚀 Quick Start

### Install Dependencies

```bash
# Install test dependencies
pip install -e ".[test]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gvit --cov-report=html
open tests/htmlcov/index.html
```

### Current Status

- ✅ **49 tests** passing (38 unit + 11 integration).
- ✅ **33% coverage** (target: 80%+).
- ✅ **Fully isolated** (no system side effects).

---

## 📁 Test Structure

```
tests/
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_env_registry.py    # EnvRegistry class tests
│   ├── test_backends/          # Backend implementations
│   └── test_utils/
│       └── test_utils.py       # Utility functions
├── integration/                # Integration tests (e2e)
│   └── test_envs.py            # `gvit envs` commands
├── fixtures/                   # Test data
├── conftest.py                 # Shared fixtures
├── .coverage                   # Coverage data (generated)
├── coverage.xml                # Coverage XML (generated)
├── htmlcov/                    # Coverage HTML (generated)
└── README.md                   # This file
```

### Test Organization

**Unit Tests (38):**
- `test_env_registry.py` - 14 tests for EnvRegistry.
- `test_utils.py` - 24 tests for utilities.

**Integration Tests (11):**
- `test_envs.py` - Commands: list, delete, prune, show-activate, show-deactivate.

---

## 🏃 Running Tests

### Basic Commands

```bash
# All tests
pytest

# With verbose output
pytest -v

# Stop at first failure
pytest -x

# Show print statements
pytest -s
```

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific file
pytest tests/unit/test_env_registry.py

# Specific test
pytest tests/unit/test_env_registry.py::TestEnvRegistry::test_list_environments_empty

# Pattern matching
pytest -k "test_list"
```

### With Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run venv-specific tests
pytest -m venv
```

**Available markers:**
- `unit` - Unit tests (fast, isolated).
- `integration` - Integration tests (slower).
- `slow` - Long-running tests.
- `venv`, `conda`, `virtualenv` - Backend-specific.

---

## ✍️ Writing Tests

### Unit Test Example

```python
def test_extract_repo_name_from_url():
    """Test extracting repo name from HTTPS URL."""
    url = "https://github.com/user/repo.git"
    assert extract_repo_name_from_url(url) == "repo"
```

**Unit tests should:**
- ✅ Be fast (< 1 second each).
- ✅ Test single function/method.
- ✅ Use mocks for external deps.
- ✅ Be completely isolated.

### Integration Test Example

```python
from typer.testing import CliRunner
from gvit.cli import app

runner = CliRunner()

def test_envs_list_command(temp_config_dir, temp_repo):
    """Test 'gvit envs list' command."""
    result = runner.invoke(app, ["envs", "list"])
    assert result.exit_code == 0
    assert "No environments in registry" in result.output
```

**Integration tests should:**
- ✅ Test complete workflows.
- ✅ Use `CliRunner` for CLI.
- ✅ Mock only external services.
- ✅ Use temp directories.

### Test Isolation

Every test runs in complete isolation:
- Temporary config directories.
- Temporary git repos.
- Mocked subprocess calls.
- No side effects on system.

This is achieved by the `isolate_tests` auto-use fixture in `conftest.py`.

---

## 📊 Coverage

### Understanding Coverage Files

Coverage reports are generated in the `tests/` directory:

| File | Purpose | Commit? |
|------|---------|---------|
| `tests/.coverage` | Binary data (SQLite) | ❌ No |
| `tests/coverage.xml` | XML for CI/CD tools | ❌ No |
| `tests/htmlcov/` | Interactive HTML report | ❌ No |

### Viewing Coverage

```bash
# Run tests with coverage
pytest

# Open HTML report
open tests/htmlcov/index.html

# Terminal report only
pytest --cov=src/gvit --cov-report=term-missing

# Single module
pytest --cov=src/gvit/env_registry.py --cov-report=term-missing

# With minimum threshold
pytest --cov=src/gvit --cov-fail-under=80
```

### HTML Coverage Report Features

- 📊 Overview with % per module.
- 🔍 Line-by-line highlighting (green=covered, red=not covered).
- 🎯 Branch coverage visualization.
- 📈 Trends (if history saved).

### Coverage Levels

- 🔴 **< 60%** - Insufficient, risky.
- 🟡 **60-80%** - Acceptable, improvable.
- 🟢 **80-90%** - Good, professional level.
- 💎 **> 90%** - Excellent, high confidence.

### Interpreting Coverage

```python
# Example: 75% coverage
def suma(a, b):          # Covered ✅
    if a < 0:            # Covered ✅
        return 0         # NOT covered ❌ (branch not tested)
    return a + b         # Covered ✅

# Test only covers positive case
def test_suma():
    assert suma(5, 3) == 8
```

**Coverage = 3/4 lines = 75%**

To reach 100%:
```python
def test_suma_negativo():
    assert suma(-5, 3) == 0  # Now covers negative branch
```

### Advanced Coverage

```bash
# Branch coverage (if/else paths)
pytest --cov=src/gvit --cov-branch

# Combine multiple runs
pytest tests/unit/ --cov=src/gvit
pytest tests/integration/ --cov=src/gvit --cov-append
coverage report

# Exclude code from coverage
def debug_func():  # pragma: no cover
    print("Debug")
```

### Coverage Configuration

Configuration is in `.coveragerc`:

```ini
[run]
source = src/gvit              # What to measure
data_file = tests/.coverage    # Where to store data
omit = */tests/*               # What to exclude

[html]
directory = tests/htmlcov      # HTML output location

[xml]
output = tests/coverage.xml    # XML output location
```

---

## 🔧 Fixtures

Common fixtures available in `conftest.py`:

### Directory Fixtures

```python
def test_example(temp_dir):
    """temp_dir: Temporary directory"""
    assert temp_dir.exists()

def test_example(temp_repo):
    """temp_repo: Initialized git repository"""
    assert (temp_repo / ".git").exists()

def test_example(temp_config_dir):
    """temp_config_dir: Isolated gvit config directory"""
    assert temp_config_dir.exists()
```

### Data Fixtures

```python
def test_example(sample_config):
    """sample_config: Sample gvit config file"""
    # Returns path to config.toml

def test_example(sample_requirements):
    """sample_requirements: Sample requirements.txt"""
    # Returns path to requirements file

def test_example(sample_env_info):
    """sample_env_info: Sample environment dict"""
    # Returns complete env info structure
```

### Service Fixtures

```python
def test_example(env_registry):
    """env_registry: EnvRegistry instance"""
    envs = env_registry.list_environments()

def test_example(mock_venv_creation, mocker):
    """mock_venv_creation: Mocked subprocess.run"""
    # Prevents actual venv creation
```

### Auto-used Fixtures

- `isolate_tests` - Automatically patches all paths for isolation

---

### Coverage Services

Compatible with:
- [Codecov](https://codecov.io/)
- [Coveralls](https://coveralls.io/)
- [SonarQube](https://www.sonarqube.org/)

---

## ✅ Best Practices

### DO:

✅ **Descriptive names** - `test_load_config_from_file` not `test_1`.  
✅ **One concept per test** - Test one thing at a time.  
✅ **Use fixtures** - DRY principle for setup.  
✅ **Test edge cases** - Empty strings, None, negative numbers.  
✅ **Test error paths** - Not just happy path.  
✅ **Independent tests** - No shared state.  
✅ **Fast unit tests** - Keep under 1 second.  
✅ **Clear assertions** - Explicit expected values.  

### DON'T:

❌ **Sleep in tests** - Use mocks instead.  
❌ **Test implementation** - Test behavior.  
❌ **Share state** - Each test isolated.  
❌ **Ignore failures** - Fix or remove.  
❌ **100% coverage obsession** - Quality > quantity.  

### Coverage Tips

1. **Prioritize important code** - Business logic first.
2. **Coverage ≠ quality** - Can have 100% with bad tests.
3. **Use HTML report** - Visual identification of gaps.
4. **Monitor trends** - Track coverage over time.

---

## 🐛 Troubleshooting

### "Config directory not found"

**Cause:** `isolate_tests` fixture not patching correctly  
**Solution:** Check that monkeypatch is working in conftest.py

### Git errors in tests

**Cause:** Git not installed or temp_repo fixture issue  
**Solution:** 
```bash
# Ensure git is installed
git --version

# Check temp_repo fixture in conftest.py
```

### Import errors

**Cause:** Package not installed in editable mode  
**Solution:**
```bash
pip install -e ".[test]"
```

### Tests passing locally but failing in CI

**Cause:** Environment differences  
**Solution:**
- Check Python version compatibility
- Verify all dependencies in pyproject.toml
- Check for absolute paths in code

### Slow tests

**Solution:**
```bash
# Identify slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
```

---

## 🎯 Next Steps

### Areas Needing Tests

1. **Backends** - venv, conda, virtualenv operations.
2. **Commands** - clone, init, setup, pull, commit, status.
3. **Git integration** - git operations and fallback.
4. **Dependency management** - install, validate, sync.
5. **Error handling** - edge cases and failures.

### Adding Tests

1. Identify code to test.
2. Choose unit vs integration.
3. Write test with clear name + docstring.
4. Use appropriate fixtures.
5. Assert expected behavior.
6. Run to verify passing.
7. Check coverage impact.

---

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [Typer testing guide](https://typer.tiangolo.com/tutorial/testing/)
- [Coverage.py docs](https://coverage.readthedocs.io/)

---

## 📈 Current Status

**Tests:** 49 passing (38 unit + 11 integration)  
**Coverage:** 33% (target: 80%+)  
**Status:** ✅ Fully functional  
**Last Updated:** 2025-11-03

---

**Tech Stack:** pytest • pytest-cov • pytest-mock • typer.testing  
**Configuration:** `pytest.ini` • `.coveragerc`  
**Location:** All coverage files in `tests/` directory
