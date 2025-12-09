# Development Setup Guide

## Project Structure

This project uses modern Python tooling:
- **pyproject.toml**: Central configuration for project metadata, dependencies, and tools
- **requirements.txt**: Pinned versions for production dependencies
- **dev-requirements.txt**: Pinned versions for development dependencies
- **Makefile**: Convenient commands for development workflow

## Quick Start

### 1. Install Dependencies

```bash
# Install production dependencies
make install

# Install development dependencies (includes testing, linting, type checking)
make dev-install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
vim .env

# Copy example config
cp config.example.yaml config.yaml

# Edit config with your filters
vim config.yaml
```

### 3. Run the Application

```bash
# Start the webhook server
make run
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run with coverage report
make test-cov
```

### Code Quality

```bash
# Check code style (no changes)
make lint

# Check and auto-fix issues
make lint-fix

# Format code
make format

# Type checking
make type-check

# Run all checks (lint + tests)
make check
```

## Tool Configuration

### Ruff (Linting & Formatting)

Configuration in `pyproject.toml` under `[tool.ruff]`:
- Target: Python 3.14+
- Line length: 100 characters
- Enabled rules: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear, comprehensions, simplify
- Double quotes for strings
- Auto-fix enabled

### Pytest (Testing)

Configuration in `pyproject.toml` under `[tool.pytest.ini_options]`:
- Test directory: `tests/`
- Markers: `unit`, `integration`, `slow`
- Verbose output with short tracebacks

### Coverage (Code Coverage)

Configuration in `pyproject.toml` under `[tool.coverage]`:
- Source: `helpers/` directory
- Branch coverage enabled
- HTML report in `htmlcov/`
- Excludes test files and common boilerplate

### MyPy (Type Checking - Optional)

Configuration in `pyproject.toml` under `[tool.mypy]`:
- Target: Python 3.14
- Strict optional checking
- Warnings enabled for unused configs and redundant casts
- Missing imports ignored (for third-party libraries)

## Dependency Management

### Philosophy

- **pyproject.toml**: Defines dependencies without version pins (flexible)
- **requirements.txt**: Pinned versions for reproducible production builds
- **dev-requirements.txt**: Pinned versions for reproducible development environments

### Adding New Dependencies

1. **Production dependency**:
   ```bash
   # Add to pyproject.toml dependencies list
   vim pyproject.toml
   
   # Install and generate pinned version
   pip install <package>
   pip freeze | grep <package> >> requirements.txt
   ```

2. **Development dependency**:
   ```bash
   # Add to pyproject.toml [project.optional-dependencies] dev list
   vim pyproject.toml
   
   # Install and generate pinned version
   pip install <package>
   pip freeze | grep <package> >> dev-requirements.txt
   ```

### Updating Dependencies

```bash
# Update a specific package
pip install --upgrade <package>
pip freeze | grep <package>  # Update version in requirements.txt

# Update all packages (carefully!)
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

## IDE Configuration

### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

### PyCharm

1. Go to Settings → Tools → Python Integrated Tools
2. Set Default test runner to `pytest`
3. Go to Settings → Tools → File Watchers
4. Add Ruff for auto-formatting on save

## Pre-commit Hooks (Optional)

You can add pre-commit hooks to automatically run checks:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see example below)
# Install hooks
pre-commit install
```

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

## Continuous Integration

The project includes GitHub Actions workflows:
- **Docker Build**: Builds and publishes Docker images
- **Tests** (optional): Run tests on push/PR

To add a test workflow, create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r dev-requirements.txt
      
      - name: Lint with ruff
        run: ruff check .
      
      - name: Run tests
        run: pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting

### Import errors
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
make install
```

### Ruff not found
```bash
# Install dev dependencies
make dev-install
```

### Tests failing
```bash
# Check if all dependencies are installed
pip list

# Clear pytest cache
rm -rf .pytest_cache
rm -rf htmlcov
rm -f .coverage

# Run tests with verbose output
pytest -vv
```

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
