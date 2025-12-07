"""Unit tests for FilterEngine"""

from helpers.filter_engine import FilterEngine


class TestFilterEngineConditions:
    """Test filter condition evaluation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FilterEngine()

    def test_contains_condition_string(self):
        """Test contains condition with string values"""
        assert self.engine.evaluate_condition("Hello World", "contains", "world")
        assert self.engine.evaluate_condition("Hello World", "contains", "hello")
        assert not self.engine.evaluate_condition("Hello World", "contains", "goodbye")

    def test_contains_condition_list(self):
        """Test contains condition with list values"""
        files = ["src/main.py", "tests/test_main.py", "README.md"]
        assert self.engine.evaluate_condition(files, "contains", "main.py")
        assert self.engine.evaluate_condition(files, "contains", "test_")
        assert not self.engine.evaluate_condition(files, "contains", "config.yaml")

    def test_contains_condition_list_of_values(self):
        """Test contains condition with list of search values"""
        text = "This is a production deployment"
        assert self.engine.evaluate_condition(
            text, "contains", ["production", "staging"]
        )
        assert self.engine.evaluate_condition(
            text, "contains", ["deploy", "deployment"]
        )
        assert not self.engine.evaluate_condition(
            text, "contains", ["test", "development"]
        )

    def test_equals_condition(self):
        """Test equals condition"""
        assert self.engine.evaluate_condition("opened", "equals", "opened")
        assert self.engine.evaluate_condition("OPENED", "equals", "opened")
        assert not self.engine.evaluate_condition("closed", "equals", "opened")

    def test_in_condition(self):
        """Test in condition"""
        assert self.engine.evaluate_condition("bug", "in", ["bug", "feature", "docs"])
        assert not self.engine.evaluate_condition("security", "in", ["bug", "feature"])

    def test_regex_condition(self):
        """Test regex condition"""
        assert self.engine.evaluate_condition("JIRA-123", "regex", r"^JIRA-\d+$")
        assert self.engine.evaluate_condition("feature/new-ui", "regex", r"^feature/")
        assert not self.engine.evaluate_condition("hotfix", "regex", r"^feature/")

    def test_greater_than_condition(self):
        """Test greater_than condition"""
        assert self.engine.evaluate_condition(100, "greater_than", 50)
        assert not self.engine.evaluate_condition(25, "greater_than", 50)
        assert not self.engine.evaluate_condition(50, "greater_than", 50)

    def test_less_than_condition(self):
        """Test less_than condition"""
        assert self.engine.evaluate_condition(25, "less_than", 50)
        assert not self.engine.evaluate_condition(100, "less_than", 50)
        assert not self.engine.evaluate_condition(50, "less_than", 50)

    def test_starts_with_condition(self):
        """Test starts_with condition"""
        assert self.engine.evaluate_condition(
            "feature/new-ui", "starts_with", "feature/"
        )
        assert not self.engine.evaluate_condition(
            "hotfix/bug", "starts_with", "feature/"
        )

    def test_ends_with_condition(self):
        """Test ends_with condition"""
        assert self.engine.evaluate_condition("config.yaml", "ends_with", ".yaml")
        assert self.engine.evaluate_condition("main.py", "ends_with", ".py")
        assert not self.engine.evaluate_condition("README.md", "ends_with", ".py")

    def test_none_value_returns_false(self):
        """Test that None values return False"""
        assert not self.engine.evaluate_condition(None, "contains", "test")
        assert not self.engine.evaluate_condition(None, "equals", "test")


class TestFilterEngineFilters:
    """Test complete filter evaluation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FilterEngine()

    def test_simple_filter_match(self):
        """Test simple filter matching"""
        filter_config = {
            "name": "Bug Issues",
            "events": ["issues"],
            "conditions": {"issue_title": {"contains": "bug"}},
        }

        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Fix bug in login",
            "repository": "org/repo",
        }

        result = self.engine.evaluate_filter(event_data, filter_config, "issues")
        assert result is True

    def test_filter_no_match(self):
        """Test filter not matching"""
        filter_config = {
            "name": "Bug Issues",
            "events": ["issues"],
            "conditions": {"issue_title": {"contains": "bug"}},
        }

        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Add new feature",
            "repository": "org/repo",
        }

        result = self.engine.evaluate_filter(event_data, filter_config, "issues")
        assert result is False

    def test_filter_wrong_event_type(self):
        """Test filter with wrong event type"""
        filter_config = {
            "name": "Issue Filter",
            "events": ["issues"],
            "conditions": {"issue_title": {"contains": "bug"}},
        }

        event_data = {
            "platform": "github",
            "event_type": "pull_request",
            "pr_title": "Fix bug in login",
            "repository": "org/repo",
        }

        result = self.engine.evaluate_filter(event_data, filter_config, "pull_request")
        assert result is False

    def test_filter_multiple_conditions_and_logic(self):
        """Test filter with multiple conditions (AND logic)"""
        filter_config = {
            "name": "Critical Production Issues",
            "events": ["issues"],
            "conditions": {
                "issue_title": {"contains": "production"},
                "labels": {"contains": "critical"},
            },
        }

        # Both conditions match
        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Production server down",
            "labels": ["critical", "bug"],
        }
        assert self.engine.evaluate_filter(event_data, filter_config, "issues") is True

        # Only one condition matches
        event_data["issue_title"] = "Development server down"
        assert self.engine.evaluate_filter(event_data, filter_config, "issues") is False

    def test_filter_any_of_logic(self):
        """Test filter with any_of (OR logic)"""
        filter_config = {
            "name": "Important Issues",
            "events": ["issues"],
            "any_of": [
                {"labels": {"contains": "critical"}},
                {"issue_title": {"contains": "urgent"}},
            ],
        }

        # First condition matches
        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Normal issue",
            "labels": ["critical"],
        }
        assert self.engine.evaluate_filter(event_data, filter_config, "issues") is True

        # Second condition matches
        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Urgent: fix this",
            "labels": ["bug"],
        }
        assert self.engine.evaluate_filter(event_data, filter_config, "issues") is True

        # No condition matches
        event_data = {
            "platform": "github",
            "event_type": "issues",
            "issue_title": "Normal issue",
            "labels": ["enhancement"],
        }
        assert self.engine.evaluate_filter(event_data, filter_config, "issues") is False

    def test_filter_list_field(self):
        """Test filtering on list fields"""
        filter_config = {
            "name": "Python File Changes",
            "events": ["push"],
            "conditions": {"modified_files": {"contains": ".py"}},
        }

        event_data = {
            "platform": "github",
            "event_type": "push",
            "modified_files": ["src/main.py", "tests/test_main.py", "README.md"],
        }

        assert self.engine.evaluate_filter(event_data, filter_config, "push") is True

        event_data["modified_files"] = ["README.md", "config.yaml"]
        assert self.engine.evaluate_filter(event_data, filter_config, "push") is False


class TestFilterEngineMessageFormatting:
    """Test message formatting"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FilterEngine()

    def test_format_message_basic(self):
        """Test basic message formatting"""
        template = "Issue #{issue_number} in {repository}"
        event_data = {"issue_number": 42, "repository": "org/repo"}

        result = self.engine.format_message(template, event_data)
        assert result == "Issue #42 in org/repo"

    def test_format_message_missing_field(self):
        """Test message formatting with missing field"""
        template = "Issue #{issue_number} in {repository}"
        event_data = {"issue_number": 42}

        result = self.engine.format_message(template, event_data)
        # format_message provides default "N/A" for missing fields
        assert result == "Issue #42 in N/A"

    def test_format_message_multiline(self):
        """Test multiline message formatting"""
        template = """🚨 Alert
Repository: {repository}
Issue: #{issue_number}
Title: {issue_title}"""
        event_data = {
            "repository": "org/repo",
            "issue_number": 42,
            "issue_title": "Critical bug",
        }

        result = self.engine.format_message(template, event_data)
        assert "org/repo" in result
        assert "#42" in result
        assert "Critical bug" in result
