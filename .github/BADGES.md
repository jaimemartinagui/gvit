# README Badges Guide

## 📊 Current Badges

The README includes these badges to show project status at a glance:

### 1. Python Version
```markdown
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
```
- **Shows:** Minimum Python version required
- **Update:** When changing `requires-python` in `pyproject.toml`

### 2. PyPI Version
```markdown
[![PyPI version](https://img.shields.io/pypi/v/gvit.svg)](https://pypi.org/project/gvit/)
```
- **Shows:** Current version published on PyPI
- **Updates:** Automatically from PyPI
- **Note:** Requires package to be published first

### 3. License
```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```
- **Shows:** Project license type
- **Update:** Only if changing license

### 4. Tests Status
```markdown
[![Tests](https://img.shields.io/badge/tests-49%20passing-brightgreen.svg)](#-testing)
```
- **Shows:** Number of passing tests
- **Update manually:** After adding/removing tests
- **Current:** 49 passing (38 unit + 11 integration)

### 5. Coverage
```markdown
[![Coverage](https://img.shields.io/badge/coverage-33%25-orange.svg)](#-testing)
```
- **Shows:** Test coverage percentage
- **Update manually:** After running coverage
- **Target:** 80%+

### 6. Code Style
```markdown
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```
- **Shows:** Code formatting standard
- **Static:** Only update if changing formatter

## 🔄 When to Update

| Badge | Update When | How Often |
|-------|-------------|-----------|
| Python version | Change `requires-python` | Rarely |
| PyPI version | New release | Auto-updates |
| License | Change LICENSE file | Almost never |
| Tests | Add/remove tests | Each PR |
| Coverage | Coverage changes | Each PR |
| Code style | Change formatter | Almost never |

## 🚀 Future Badges (When Ready)

### GitHub Actions CI
```markdown
[![CI](https://github.com/jaimemartinagui/gvit/actions/workflows/tests.yml/badge.svg)](https://github.com/jaimemartinagui/gvit/actions)
```
**Requirements:**
1. Create `.github/workflows/tests.yml`
2. Configure GitHub Actions
3. Add badge (updates automatically)

### Codecov
```markdown
[![Coverage](https://codecov.io/gh/jaimemartinagui/gvit/branch/main/graph/badge.svg)](https://codecov.io/gh/jaimemartinagui/gvit)
```
**Requirements:**
1. Sign up at codecov.io
2. Connect GitHub repo
3. Upload coverage in CI
4. Add badge (updates automatically)

### PyPI Downloads
```markdown
[![Downloads](https://pepy.tech/badge/gvit)](https://pepy.tech/project/gvit)
```
**Requirements:**
1. Package published on PyPI
2. Wait for download stats
3. Add badge (updates automatically)

## 📝 Badge Format

All badges use shields.io format:

```
https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>.svg
```

### Colors
- `brightgreen` - Success/passing
- `green` - Good
- `yellowgreen` - OK
- `orange` - Warning
- `red` - Error/failing
- `blue` - Info
- `lightgrey` - Neutral

### Custom Badges

Create custom badges at: https://shields.io/

Example:
```markdown
[![Custom](https://img.shields.io/badge/custom-message-color.svg)](https://link.com)
```

## 🔧 Maintenance

### Checklist for Releases

- [ ] Update version in `pyproject.toml`
- [ ] Run tests: `pytest`
- [ ] Check coverage: `pytest --cov=src/gvit`
- [ ] Update Tests badge in README (if count changed)
- [ ] Update Coverage badge in README (if % changed)
- [ ] Commit changes
- [ ] Create git tag
- [ ] Publish to PyPI (PyPI badge auto-updates)

### Quick Update Commands

```bash
# Get test count
pytest --co -q | tail -1

# Get coverage percentage
pytest --cov=src/gvit --cov-report=term | grep TOTAL

# Update README badges manually
# Then commit
git add README.md
git commit -m "docs: update badges"
```

## 🎨 Badge Positioning

Badges are in `<div align="center">` for centered layout:

```markdown
<div align="center">

**Title**

Description

[![Badge1](url)](link)
[![Badge2](url)](link)

</div>
```

## 📚 Resources

- [Shields.io](https://shields.io/) - Badge generator
- [Simple Icons](https://simpleicons.org/) - Icons for badges
- [Badges Guide](https://github.com/badges/shields) - Complete documentation

---

**Last Updated:** 2025-01-03  
**Current Badges:** 6 (3 auto, 3 manual)
