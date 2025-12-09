# Quick Reference: pyproject.toml Setup

## 📁 File Structure
```
├── pyproject.toml           # Central config (metadata, tools)
├── requirements.txt         # Pinned production deps
├── dev-requirements.txt     # Pinned dev deps
├── Makefile                 # Development commands
└── .env                     # Secrets (not in git)
```

## 🚀 Quick Commands

```bash
# Setup
make install          # Install production dependencies
make dev-install      # Install dev dependencies

# Development
make run             # Start server
make test            # Run all tests
make test-cov        # Run tests with coverage
make lint            # Check code style
make lint-fix        # Fix linting issues
make format          # Format code
make type-check      # Run type checker
make check           # Run all checks

# Cleanup
make clean           # Remove venv and cache
make stop            # Stop server
```

## 📦 Adding Dependencies

### Production Dependency
```bash
# 1. Add to pyproject.toml [project] dependencies
# 2. Install and pin version
pip install <package>
pip freeze | grep <package> >> requirements.txt
```

### Dev Dependency
```bash
# 1. Add to pyproject.toml [project.optional-dependencies] dev
# 2. Install and pin version
pip install <package>
pip freeze | grep <package> >> dev-requirements.txt
```

## ⚙️ Tool Configuration Locations

| Tool | Configuration Location |
|------|----------------------|
| Ruff | `[tool.ruff]` in pyproject.toml |
| Pytest | `[tool.pytest.ini_options]` in pyproject.toml |
| Coverage | `[tool.coverage.*]` in pyproject.toml |
| MyPy | `[tool.mypy]` in pyproject.toml |
| Project | `[project]` in pyproject.toml |

## 🔧 Key Settings

### Ruff
- Line length: 100
- Python target: 3.11+
- Auto-fix: Enabled
- Quote style: Double

### Pytest
- Test path: `tests/`
- Markers: `unit`, `integration`, `slow`
- Coverage source: `helpers/`

## 🐳 Docker

```bash
# Build
docker build -t webhook-handler .

# Run
docker-compose up -d

# Uses requirements.txt for pinned versions
```

## 📚 Documentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - Full development guide
- [MIGRATION.md](MIGRATION.md) - Migration details
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [CI-CD.md](CI-CD.md) - CI/CD pipeline guide
