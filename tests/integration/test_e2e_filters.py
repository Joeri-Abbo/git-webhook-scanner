"""End-to-end integration tests with filters and notifications"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import Mock
from flask import Flask
from helpers.handler.github import GitHubWebhookHandler
from helpers.notification.slack import SlackNotification


@pytest.fixture
def mock_notification_manager():
    """Create a mock notification manager"""
    manager = Mock(spec=SlackNotification)
    manager.send = Mock()
    return manager


@pytest.fixture
def github_app_with_filters(mock_notification_manager):
    """Create Flask app with GitHub handler and filters"""
    app = Flask(__name__)
    app.config["TESTING"] = True

    filters = [
        {
            "name": "Bug Issues",
            "platform": ["github"],
            "events": ["issues"],
            "conditions": {"issue_title": {"contains": "bug"}},
            "notify": True,
            "message": "🐛 Bug reported: {issue_title} in {repository}",
        },
        {
            "name": "Large PRs",
            "platform": ["github"],
            "events": ["pull_request"],
            "conditions": {"pr_changes": {"greater_than": 10}},
            "notify": True,
            "message": "⚠️ Large PR: {pr_title} ({pr_changes} files)",
        },
        {
            "name": "Production Changes",
            "platform": ["github"],
            "events": ["push"],
            "conditions": {"ref": {"equals": "refs/heads/production"}},
            "notify": True,
            "message": "🚀 Push to production by {sender}",
        },
    ]

    handler = GitHubWebhookHandler(
        app=app,
        endpoint="/github/webhook",
        secret="test-secret",
        notification_manager=mock_notification_manager,
        filters=filters,
    )

    return app, handler, mock_notification_manager


class TestEndToEndWithFilters:
    """Test complete webhook processing with filters and notifications"""

    def test_bug_issue_triggers_notification(self, github_app_with_filters):
        """Test that bug issues trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Fix bug in authentication",
                "body": "Users cannot log in",
                "html_url": "https://github.com/org/repo/issues/42",
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
                "X-Github-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204
        mock_notif.send.assert_called_once()
        call_args = mock_notif.send.call_args[0][0]
        assert "Fix bug in authentication" in call_args
        assert "org/repo" in call_args

    def test_non_bug_issue_no_notification(self, github_app_with_filters):
        """Test that non-bug issues don't trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "action": "opened",
            "issue": {
                "number": 43,
                "title": "Add new feature",
                "body": "Feature request",
                "html_url": "https://github.com/org/repo/issues/43",
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
                "X-Github-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204
        mock_notif.send.assert_not_called()

    def test_large_pr_triggers_notification(self, github_app_with_filters):
        """Test that large PRs trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 100,
                "title": "Refactor authentication module",
                "body": "Major refactoring",
                "html_url": "https://github.com/org/repo/pull/100",
                "changed_files": 25,
                "state": "open",
                "base": {"ref": "main"},
                "head": {"ref": "refactor"},
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
        mock_notif.send.assert_called_once()
        call_args = mock_notif.send.call_args[0][0]
        assert "25 files" in call_args

    def test_small_pr_no_notification(self, github_app_with_filters):
        """Test that small PRs don't trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 101,
                "title": "Fix typo",
                "body": "Minor fix",
                "html_url": "https://github.com/org/repo/pull/101",
                "changed_files": 2,
                "state": "open",
                "base": {"ref": "main"},
                "head": {"ref": "fix-typo"},
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
        mock_notif.send.assert_not_called()

    def test_production_push_triggers_notification(self, github_app_with_filters):
        """Test that production pushes trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "ref": "refs/heads/production",
            "commits": [
                {
                    "message": "Deploy v1.2.3",
                    "added": [],
                    "modified": ["version.txt"],
                    "removed": [],
                }
            ],
            "compare": "https://github.com/org/repo/compare/abc...def",
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "deployer"},
            "pusher": {"name": "deployer"},
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
                "X-Github-Event": "push",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204
        mock_notif.send.assert_called_once()
        call_args = mock_notif.send.call_args[0][0]
        assert "production" in call_args.lower()
        assert "deployer" in call_args

    def test_non_production_push_no_notification(self, github_app_with_filters):
        """Test that non-production pushes don't trigger notifications"""
        app, handler, mock_notif = github_app_with_filters
        client = app.test_client()

        payload = {
            "ref": "refs/heads/develop",
            "commits": [
                {
                    "message": "Work in progress",
                    "added": ["new_file.py"],
                    "modified": [],
                    "removed": [],
                }
            ],
            "compare": "https://github.com/org/repo/compare/abc...def",
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "developer"},
            "pusher": {"name": "developer"},
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
                "X-Github-Event": "push",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 204
        mock_notif.send.assert_not_called()
