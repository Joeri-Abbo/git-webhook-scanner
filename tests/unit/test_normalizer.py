"""Unit tests for EventNormalizer"""

from helpers.normalizer import EventNormalizer


class TestGitHubNormalization:
    """Test GitHub event normalization"""

    def test_normalize_issue_opened(self):
        """Test normalization of GitHub issue opened event"""
        github_data = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Bug in feature X",
                "body": "Description of the bug",
                "html_url": "https://github.com/org/repo/issues/42",
                "labels": [{"name": "bug"}, {"name": "priority-high"}],
            },
            "repository": {
                "full_name": "org/repo",
                "description": "Test repository",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "testuser"},
        }

        result = EventNormalizer.normalize_github(github_data, "issues")

        assert result["platform"] == "github"
        assert result["event_type"] == "issues"
        assert result["action"] == "opened"
        assert result["repository"] == "org/repo"
        assert result["repository_description"] == "Test repository"
        assert result["sender"] == "testuser"
        assert result["issue_number"] == 42
        assert result["issue_title"] == "Bug in feature X"
        assert result["issue_body"] == "Description of the bug"
        assert result["labels"] == ["bug", "priority-high"]

    def test_normalize_pull_request_opened(self):
        """Test normalization of GitHub PR opened event"""
        github_data = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Add new feature",
                "body": "This PR adds feature Y",
                "html_url": "https://github.com/org/repo/pull/123",
                "changed_files": 5,
                "state": "open",
                "base": {"ref": "main"},
                "head": {"ref": "feature-y"},
                "labels": [{"name": "enhancement"}],
            },
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "developer"},
        }

        result = EventNormalizer.normalize_github(github_data, "pull_request")

        assert result["platform"] == "github"
        assert result["event_type"] == "pull_request"
        assert result["pr_number"] == 123
        assert result["pr_title"] == "Add new feature"
        assert result["pr_changes"] == 5
        assert result["target_branch"] == "main"
        assert result["source_branch"] == "feature-y"
        assert result["labels"] == ["enhancement"]

    def test_normalize_push_event(self):
        """Test normalization of GitHub push event"""
        github_data = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "message": "Fix typo",
                    "added": ["file1.py"],
                    "modified": ["file2.py"],
                    "removed": [],
                    "html_url": "https://github.com/org/repo/commit/abc123",
                },
                {
                    "message": "Update docs",
                    "added": [],
                    "modified": ["README.md"],
                    "removed": ["OLD.md"],
                    "html_url": "https://github.com/org/repo/commit/def456",
                },
            ],
            "compare": "https://github.com/org/repo/compare/abc...def",
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "developer"},
            "pusher": {"name": "developer"},
        }

        result = EventNormalizer.normalize_github(github_data, "push")

        assert result["platform"] == "github"
        assert result["event_type"] == "push"
        assert result["ref"] == "refs/heads/main"
        assert result["commits"] == 2
        assert result["pusher"] == "developer"
        assert "file1.py" in result["modified_files"]
        assert "file2.py" in result["modified_files"]
        assert "README.md" in result["modified_files"]
        assert "OLD.md" in result["modified_files"]
        assert len(result["commit_messages"]) == 2
        assert result["compare_url"] == "https://github.com/org/repo/compare/abc...def"

    def test_normalize_workflow_run_event(self):
        """Test normalization of GitHub workflow run event"""
        github_data = {
            "action": "completed",
            "workflow_run": {
                "name": "CI Build",
                "status": "completed",
                "conclusion": "failure",
            },
            "repository": {
                "full_name": "org/repo",
                "html_url": "https://github.com/org/repo",
            },
            "sender": {"login": "github-actions"},
        }

        result = EventNormalizer.normalize_github(github_data, "workflow_run")

        assert result["platform"] == "github"
        assert result["workflow_name"] == "CI Build"
        assert result["workflow_status"] == "completed"
        assert result["workflow_conclusion"] == "failure"


class TestGitLabNormalization:
    """Test GitLab event normalization"""

    def test_normalize_issue_opened(self):
        """Test normalization of GitLab issue opened event"""
        gitlab_data = {
            "object_kind": "issue",
            "object_attributes": {
                "iid": 42,
                "title": "Bug in feature X",
                "description": "Description of the bug",
                "url": "https://gitlab.com/org/repo/-/issues/42",
                "action": "open",
            },
            "labels": [{"title": "bug"}, {"title": "priority-high"}],
            "project": {
                "path_with_namespace": "org/repo",
                "description": "Test repository",
                "web_url": "https://gitlab.com/org/repo",
            },
            "user": {"username": "testuser"},
        }

        result = EventNormalizer.normalize_gitlab(gitlab_data, "issue")

        assert result["platform"] == "gitlab"
        assert result["event_type"] == "issue"
        assert result["action"] == "open"
        assert result["repository"] == "org/repo"
        assert result["sender"] == "testuser"
        assert result["issue_number"] == 42
        assert result["issue_title"] == "Bug in feature X"
        assert result["labels"] == ["bug", "priority-high"]

    def test_normalize_merge_request_opened(self):
        """Test normalization of GitLab MR opened event"""
        gitlab_data = {
            "object_kind": "merge_request",
            "object_attributes": {
                "iid": 123,
                "title": "Add new feature",
                "description": "This MR adds feature Y",
                "url": "https://gitlab.com/org/repo/-/merge_requests/123",
                "action": "open",
                "state": "opened",
                "target_branch": "main",
                "source_branch": "feature-y",
            },
            "changes": {"total": 5},
            "project": {
                "path_with_namespace": "org/repo",
                "web_url": "https://gitlab.com/org/repo",
            },
            "user": {"username": "developer"},
            "labels": [{"title": "enhancement"}],
        }

        result = EventNormalizer.normalize_gitlab(gitlab_data, "merge_request")

        assert result["platform"] == "gitlab"
        assert result["event_type"] == "merge_request"
        assert result["pr_number"] == 123
        assert result["pr_title"] == "Add new feature"
        assert result["target_branch"] == "main"
        assert result["source_branch"] == "feature-y"

    def test_normalize_push_event(self):
        """Test normalization of GitLab push event"""
        gitlab_data = {
            "object_kind": "push",
            "ref": "refs/heads/main",
            "total_commits_count": 2,
            "commits": [
                {
                    "message": "Fix typo",
                    "added": ["file1.py"],
                    "modified": ["file2.py"],
                },
                {"message": "Update docs", "modified": ["README.md"]},
            ],
            "project": {
                "path_with_namespace": "org/repo",
                "web_url": "https://gitlab.com/org/repo",
            },
            "user_name": "developer",
        }

        result = EventNormalizer.normalize_gitlab(gitlab_data, "push")

        assert result["platform"] == "gitlab"
        assert result["event_type"] == "push"
        assert result["ref"] == "refs/heads/main"
        assert result["commits"] == 2
        assert result["sender"] == "developer"
        assert "file1.py" in result["modified_files"]
        assert "file2.py" in result["modified_files"]
