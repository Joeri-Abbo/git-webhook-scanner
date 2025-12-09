.PHONY: install dev-install run forward test test-unit test-integration test-cov lint format clean help

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
RUFF = $(VENV)/bin/ruff
PYTEST = $(VENV)/bin/pytest

help:
	@echo "GitHub/GitLab Webhook Handler - Available commands:"
	@echo ""
	@echo "  make install        - Create virtual environment and install dependencies"
	@echo "  make dev-install    - Install development dependencies (testing, linting)"
	@echo "  make run            - Start the webhook server with auto-reload"
	@echo "  make forward        - Start ngrok tunnel (for local development)"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make lint           - Run ruff linter"
	@echo "  make lint-fix       - Run ruff linter with auto-fix"
	@echo "  make format         - Format code with ruff"
	@echo "  make check          - Run all checks (lint + test)"
	@echo "  make type-check     - Run mypy type checker"
	@echo "  make clean          - Remove virtual environment and cache files"
	@echo "  make stop           - Stop the webhook server"
	@echo ""

install:
	@echo "Creating virtual environment..."
	@test -d $(VENV) || python3 -m venv $(VENV)
	@echo "Installing dependencies..."
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -r requirements.txt
	@echo ""
	@echo "Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and configure your secrets"
	@echo "2. Edit config.yaml to configure your filters"
	@echo "3. Run 'make run' to start the server"

dev-install: install
	@echo "Installing development dependencies..."
	@$(PIP) install -r dev-requirements.txt
	@echo ""
	@echo "Development dependencies installed!"
	@echo ""
	@echo "You can now:"
	@echo "  - Run tests with 'make test'"
	@echo "  - Run linting with 'make lint'"
	@echo "  - Format code with 'make format'"
	@echo "  - Run type checking with 'make type-check'"

run:
	@echo "Starting webhook server on http://0.0.0.0:8000"
	@$(UVICORN) main:asgi_app --host 0.0.0.0 --port 8000 --reload

forward:
	@echo "Starting ngrok tunnel to localhost:8000"
	@ngrok http 8000

test:
	@echo "Running all tests..."
	@$(PYTEST) -v

test-unit:
	@echo "Running unit tests..."
	@$(PYTEST) tests/unit -v

test-integration:
	@echo "Running integration tests..."
	@$(PYTEST) tests/integration -v

test-cov:
	@echo "Running tests with coverage..."
	@$(PYTEST) --cov=helpers --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running ruff linter..."
	@$(RUFF) check .

lint-fix:
	@echo "Running ruff linter with auto-fix..."
	@$(RUFF) check . --fix

format:
	@echo "Formatting code with ruff..."
	@$(RUFF) format .
	@echo "Code formatted!"

check: lint test
	@echo "All checks passed!"

type-check:
	@echo "Running mypy type checker..."
	@$(VENV)/bin/mypy helpers/ main.py || echo "Type checking complete (warnings may exist)"

stop:
	@echo "Stopping webhook server..."
	@pkill -f "uvicorn main:asgi_app" || echo "Server not running"

clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV)
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"
