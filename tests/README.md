# Tests

This directory contains the test suite for the Unified Webhook Handler.

## Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests
│   ├── test_normalizer.py   # EventNormalizer tests
│   ├── test_filter_engine.py # FilterEngine tests
│   └── test_notifications.py # Notification system tests
└── integration/             # Integration tests
    ├── test_webhook_handlers.py # Webhook handler tests
    └── test_e2e_filters.py      # End-to-end filter tests
```

## Running Tests

### All Tests
```bash
make test
# or
pytest
```

### Unit Tests Only
```bash
make test-unit
# or
pytest tests/unit
```

### Integration Tests Only
```bash
make test-integration
# or
pytest tests/integration
```

### With Coverage
```bash
make test-cov
# or
pytest --cov=helpers --cov-report=html
```

## Writing Tests

### Unit Tests

Unit tests should test individual components in isolation. Use mocks for external dependencies.

Example:
```python
def test_evaluate_condition():
    engine = FilterEngine()
    result = engine.evaluate_condition("hello world", "contains", "world")
    assert result is True
```

### Integration Tests

Integration tests should test multiple components working together.

Example:
```python
def test_webhook_processing(github_app):
    app, handler = github_app
    client = app.test_client()
    
    response = client.post('/github/webhook', ...)
    assert response.status_code == 200
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_github_issue_data` - Sample GitHub issue webhook payload
- `sample_github_pr_data` - Sample GitHub PR webhook payload
- `sample_gitlab_issue_data` - Sample GitLab issue webhook payload
- `sample_gitlab_mr_data` - Sample GitLab MR webhook payload
- `sample_filter_config` - Sample filter configuration

## Coverage Goals

- **Unit tests**: Aim for 80%+ coverage of core logic
- **Integration tests**: Cover main workflows and error cases
- **Critical paths**: 100% coverage for security and filter evaluation

## CI/CD

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

See `.github/workflows/test.yml` for CI configuration.
