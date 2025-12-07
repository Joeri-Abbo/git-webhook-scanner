"""Integration tests for webhook handlers"""

import pytest
import json
import hmac
import hashlib
from flask import Flask
from helpers.handler.github import GitHubWebhookHandler
from helpers.handler.gitlab import GitLabWebhookHandler


@pytest.fixture
def github_app():
    """Create a Flask app with GitHub webhook handler"""
    app = Flask(__name__)
    app.config["TESTING"] = True

    handler = GitHubWebhookHandler(
        app=app,
        endpoint="/github/webhook",
        secret="test-secret",
        notification_manager=None,
        filters=[],
    )

    return app, handler


@pytest.fixture
def gitlab_app():
    """Create a Flask app with GitLab webhook handler"""
    app = Flask(__name__)
    app.config["TESTING"] = True

    handler = GitLabWebhookHandler(
        app=app,
        endpoint="/gitlab/webhook",
        secret="test-token",
        notification_manager=None,
        filters=[],
    )

    return app, handler


class TestGitHubWebhookIntegration:
    """Integration tests for GitHub webhook handler"""

    def test_issue_opened_webhook(self, github_app):
        """Test processing GitHub issue opened webhook"""
        app, handler = github_app
        client = app.test_client()

        payload = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Test issue",
                "body": "Issue description",
                "html_url": "https://github.com/org/repo/issues/42",
                "labels": [],
            },
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "testuser"},
        }

        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = (
            "sha256="
            + hmac.new(b"test-secret", payload_bytes, hashlib.sha256).hexdigest()
        )

        response = client.post(
            "/github/webhook",
            data=payload_bytes,
            headers={
                "X-Github-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204

    def test_pull_request_opened_webhook(self, github_app):
        """Test processing GitHub PR opened webhook"""
        app, handler = github_app
        client = app.test_client()

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "body": "PR description",
                "html_url": "https://github.com/org/repo/pull/123",
                "changed_files": 3,
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

        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = (
            "sha256="
            + hmac.new(b"test-secret", payload_bytes, hashlib.sha256).hexdigest()
        )

        response = client.post(
            "/github/webhook",
            data=payload_bytes,
            headers={
                "X-Github-Event": "pull_request",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204

    def test_invalid_signature(self, github_app):
        """Test webhook with invalid signature"""
        app, handler = github_app
        client = app.test_client()

        payload = {"action": "opened", "issue": {"number": 1}}
        payload_bytes = json.dumps(payload).encode("utf-8")

        response = client.post(
            "/github/webhook",
            data=payload_bytes,
            headers={
                "X-Github-Event": "issues",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 401

    def test_missing_signature(self, github_app):
        """Test webhook with missing signature"""
        app, handler = github_app
        client = app.test_client()

        payload = {"action": "opened", "issue": {"number": 1}}

        response = client.post(
            "/github/webhook",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Github-Event": "issues",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 401


class TestGitLabWebhookIntegration:
    """Integration tests for GitLab webhook handler"""

    def test_issue_opened_webhook(self, gitlab_app):
        """Test processing GitLab issue opened webhook"""
        app, handler = gitlab_app
        client = app.test_client()

        payload = {
            "object_kind": "issue",
            "object_attributes": {
                "iid": 42,
                "title": "Test issue",
                "description": "Issue description",
                "url": "https://gitlab.com/org/repo/-/issues/42",
                "action": "open",
                "labels": [],
            },
            "project": {
                "path_with_namespace": "org/repo",
                "web_url": "https://gitlab.com/org/repo",
            },
            "user": {"username": "testuser"},
        }

        response = client.post(
            "/gitlab/webhook",
            data=json.dumps(payload),
            headers={
                "X-Gitlab-Event": "Issue Hook",
                "X-Gitlab-Token": "test-token",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204

    def test_merge_request_opened_webhook(self, gitlab_app):
        """Test processing GitLab MR opened webhook"""
        app, handler = gitlab_app
        client = app.test_client()

        payload = {
            "object_kind": "merge_request",
            "object_attributes": {
                "iid": 123,
                "title": "Test MR",
                "description": "MR description",
                "url": "https://gitlab.com/org/repo/-/merge_requests/123",
                "action": "open",
                "state": "opened",
                "target_branch": "main",
                "source_branch": "feature",
            },
            "project": {
                "path_with_namespace": "org/repo",
                "web_url": "https://gitlab.com/org/repo",
            },
            "user": {"username": "developer"},
            "labels": [],
        }

        response = client.post(
            "/gitlab/webhook",
            data=json.dumps(payload),
            headers={
                "X-Gitlab-Event": "Merge Request Hook",
                "X-Gitlab-Token": "test-token",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204

    def test_invalid_token(self, gitlab_app):
        """Test webhook with invalid token"""
        app, handler = gitlab_app
        client = app.test_client()

        payload = {"object_kind": "issue"}

        response = client.post(
            "/gitlab/webhook",
            data=json.dumps(payload),
            headers={
                "X-Gitlab-Event": "Issue Hook",
                "X-Gitlab-Token": "wrong-token",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 401

    def test_missing_token(self, gitlab_app):
        """Test webhook with missing token"""
        app, handler = gitlab_app
        client = app.test_client()

        payload = {"object_kind": "issue"}

        response = client.post(
            "/gitlab/webhook",
            data=json.dumps(payload),
            headers={
                "X-Gitlab-Event": "Issue Hook",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 401
