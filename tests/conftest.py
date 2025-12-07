"""Pytest fixtures and configuration"""

import pytest
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def sample_github_issue_data():
    """Sample GitHub issue webhook data"""
    return {
        "action": "opened",
        "issue": {
            "number": 42,
            "title": "Test issue",
            "body": "Issue description",
            "html_url": "https://github.com/org/repo/issues/42",
            "labels": [{"name": "bug"}],
        },
        "repository": {
            "full_name": "org/repo",
            "description": "Test repository",
            "html_url": "https://github.com/org/repo",
        },
        "sender": {"login": "testuser"},
    }


@pytest.fixture
def sample_github_pr_data():
    """Sample GitHub pull request webhook data"""
    return {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "title": "Add new feature",
            "body": "PR description",
            "html_url": "https://github.com/org/repo/pull/123",
            "changed_files": 5,
            "state": "open",
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
            "labels": [],
        },
        "repository": {
            "full_name": "org/repo",
            "html_url": "https://github.com/org/repo",
        },
        "sender": {"login": "developer"},
    }


@pytest.fixture
def sample_gitlab_issue_data():
    """Sample GitLab issue webhook data"""
    return {
        "object_kind": "issue",
        "object_attributes": {
            "iid": 42,
            "title": "Test issue",
            "description": "Issue description",
            "url": "https://gitlab.com/org/repo/-/issues/42",
            "action": "open",
            "labels": [{"title": "bug"}],
        },
        "project": {
            "path_with_namespace": "org/repo",
            "description": "Test repository",
            "web_url": "https://gitlab.com/org/repo",
        },
        "user": {"username": "testuser"},
    }


@pytest.fixture
def sample_gitlab_mr_data():
    """Sample GitLab merge request webhook data"""
    return {
        "object_kind": "merge_request",
        "object_attributes": {
            "iid": 123,
            "title": "Add new feature",
            "description": "MR description",
            "url": "https://gitlab.com/org/repo/-/merge_requests/123",
            "action": "open",
            "state": "opened",
            "target_branch": "main",
            "source_branch": "feature",
        },
        "changes": {"total": 5},
        "project": {
            "path_with_namespace": "org/repo",
            "web_url": "https://gitlab.com/org/repo",
        },
        "user": {"username": "developer"},
        "labels": [],
    }


@pytest.fixture
def sample_filter_config():
    """Sample filter configuration"""
    return {
        "name": "Test Filter",
        "platform": ["github", "gitlab"],
        "events": ["issues", "issue"],
        "conditions": {"issue_title": {"contains": "bug"}},
        "notify": True,
        "message": "Bug reported: {issue_title}",
    }
