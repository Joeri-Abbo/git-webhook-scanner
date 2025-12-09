# Migration to pyproject.toml

## Summary of Changes

This document summarizes the migration to use `pyproject.toml` for modern Python project management.

## Files Modified

### 1. **pyproject.toml** (NEW)
Central configuration file containing:
- Project metadata (name, version, description, authors)
- Dependencies list (unpinned for flexibility)
- Optional dev dependencies
- Ruff configuration (linting & formatting)
- Pytest configuration (testing)
- Coverage configuration (code coverage reporting)
- MyPy configuration (type checking - optional)

### 2. **requirements.txt** (UPDATED)
- Added version pinning with specific versions
- Organized by category (Web Framework, Configuration, HTTP, Git APIs)
- Use for Docker builds and production deployments
- Versions: Flask 3.0.3, uvicorn 0.30.6, requests 2.32.3, etc.

### 3. **dev-requirements.txt** (UPDATED)
- Added version ranges for dev tools
- Includes pytest, pytest-cov, pytest-mock, ruff, mypy
- Added type stubs for better type checking

### 4. **Makefile** (UPDATED)
New commands added:
- `make lint-fix` - Run linter with auto-fix
- `make check` - Run all checks (lint + test)
- `make type-check` - Run mypy type checker
- Updated help text with new commands

### 5. **.dockerignore** (UPDATED)
- Added `pyproject.toml` and `.ruff.toml` to exclude list
- Keeps Docker images smaller

### 6. **DEVELOPMENT.md** (NEW)
Comprehensive development guide:
- Tool configuration overview
- Dependency management philosophy
- IDE setup instructions
- Pre-commit hooks example
- CI/CD integration guide
- Troubleshooting tips

### 7. **.ruff.toml** (NEW)
- Optional dedicated Ruff config file
- Currently commented out (using pyproject.toml)
- Can be activated if preferred over pyproject.toml

### 8. **README.md** (UPDATED)
- Updated development section
- Added reference to DEVELOPMENT.md
- Updated project structure to show pyproject.toml

## Configuration Details

### Ruff (Linting & Formatting)

**Enabled Rules:**
- E, W: pycodestyle (PEP 8 style)
- F: pyflakes (logical errors)
- I: isort (import sorting)
- N: pep8-naming (naming conventions)
- UP: pyupgrade (Python syntax upgrades)
- B: flake8-bugbear (bug detection)
- C4: flake8-comprehensions (list/dict comprehension improvements)
- SIM: flake8-simplify (code simplification)
- Q: flake8-quotes (quote style enforcement)

**Settings:**
- Line length: 100 characters
- Quote style: Double quotes
- Auto-fix enabled for all rules

### Pytest (Testing)

**Configuration:**
- Test paths: `tests/`
- Markers: `unit`, `integration`, `slow`
- Verbose output with short tracebacks
- Warnings disabled by default

### Coverage (Code Coverage)

**Configuration:**
- Source: `helpers/` directory
- Branch coverage enabled
- HTML reports in `htmlcov/`
- Excludes boilerplate code (repr, main blocks, etc.)

## Dependency Philosophy

### Three-Tier Approach

1. **pyproject.toml** 
   - Defines what packages are needed
   - No version pins (flexible for development)
   - Source of truth for package list

2. **requirements.txt**
   - Pinned versions for production
   - Used in Docker builds
   - Ensures reproducible deployments

3. **dev-requirements.txt**
   - Version ranges for dev tools
   - Flexibility for newer features
   - Still constrained to avoid breaking changes

## Usage Guide

### For Developers

```bash
# Setup
make dev-install

# Development workflow
make lint-fix     # Fix linting issues
make format       # Format code
make test         # Run tests
make check        # Run all checks

# Type checking (optional)
make type-check
```

### For CI/CD

```bash
# Install exact versions
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Run checks
ruff check .
pytest --cov
```

### For Docker

```dockerfile
# Dockerfile uses requirements.txt for pinned versions
COPY requirements.txt .
RUN pip install -r requirements.txt
```

## Benefits

### ✅ Modern Python Standards
- Follows PEP 517/518/621 standards
- Single source of truth for project metadata
- Better tooling support

### ✅ Consolidated Configuration
- All tool configs in one place (pyproject.toml)
- No more scattered config files
- Easier to maintain

### ✅ Better Dependency Management
- Clear separation: flexible dev vs. pinned production
- Easier to update dependencies
- Better reproducibility

### ✅ Enhanced Development Experience
- Fast linting with Ruff (10-100x faster than flake8)
- Auto-formatting on save
- Comprehensive test coverage reporting
- Optional type checking with MyPy

### ✅ CI/CD Ready
- GitHub Actions compatible
- Docker-optimized
- Pre-commit hooks support

## Migration Notes

### What Changed
- ❌ Removed: `pytest.ini` (moved to pyproject.toml)
- ✅ Updated: Version pinning in requirements.txt
- ✅ Added: pyproject.toml with full configuration
- ✅ Enhanced: Makefile with more commands

### What Stayed the Same
- ✅ requirements.txt still used (now with pinned versions)
- ✅ dev-requirements.txt still used (now with ranges)
- ✅ Dockerfile unchanged (still uses requirements.txt)
- ✅ All existing code unchanged

### Backward Compatibility
- ✅ Existing workflows still work
- ✅ Docker builds unchanged
- ✅ No breaking changes to application code

## Next Steps

### Optional Enhancements

1. **Add Pre-commit Hooks**
   ```bash
   pip install pre-commit
   # Add .pre-commit-config.yaml (see DEVELOPMENT.md)
   pre-commit install
   ```

2. **Add Type Hints**
   ```python
   def process_webhook(data: dict) -> bool:
       ...
   ```

3. **Add GitHub Actions Test Workflow**
   - See DEVELOPMENT.md for example workflow
   - Runs tests on every push/PR

4. **Add Coverage Badge**
   ```markdown
   ![Coverage](https://img.shields.io/codecov/c/github/joeri-abbo/git-webhook-scanner)
   ```

## Resources

- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Python Packaging Guide](https://packaging.python.org/)
- [DEVELOPMENT.md](DEVELOPMENT.md) - Full development guide
