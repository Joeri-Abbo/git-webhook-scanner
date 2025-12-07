import re
from typing import Dict, Any, Optional


class FilterEngine:
    """Engine for evaluating filter conditions"""

    def __init__(self, file_content_fetcher=None):
        """Initialize filter engine with optional file content fetcher"""
        self.file_content_fetcher = file_content_fetcher

    def evaluate_condition(
        self,
        value: Any,
        condition_type: str,
        condition_value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate a single condition"""
        if value is None:
            return False

        # Handle list values (like modified_files)
        if isinstance(value, list):
            if condition_type == "contains":
                # Check if any item in the list contains the condition value
                if isinstance(condition_value, list):
                    # Check if any condition value is in any list item
                    return any(
                        any(
                            str(cv).lower() in str(item).lower()
                            for cv in condition_value
                        )
                        for item in value
                    )
                else:
                    # Check if condition value is in any list item
                    return any(
                        str(condition_value).lower() in str(item).lower()
                        for item in value
                    )
            elif condition_type == "equals":
                # Check if condition value equals any item in the list
                return any(
                    str(item).lower() == str(condition_value).lower() for item in value
                )
            elif condition_type == "in":
                # Check if any item in the list is in the condition value list
                if isinstance(condition_value, list):
                    return any(
                        str(item).lower() in [str(cv).lower() for cv in condition_value]
                        for item in value
                    )
                return False
            # For other condition types on lists, check if any item matches
            return any(
                FilterEngine.evaluate_condition(item, condition_type, condition_value)
                for item in value
            )

        # Convert value to string for text operations
        str_value = (
            str(value).lower() if isinstance(value, (str, int, float)) else str(value)
        )

        if condition_type == "equals":
            return str_value == str(condition_value).lower()

        elif condition_type == "contains":
            if isinstance(condition_value, list):
                # Check if any of the values in the list are contained
                return any(str(cv).lower() in str_value for cv in condition_value)
            else:
                return str(condition_value).lower() in str_value

        elif condition_type == "in":
            if isinstance(condition_value, list):
                return str_value in [str(cv).lower() for cv in condition_value]
            return False

        elif condition_type == "regex":
            try:
                return bool(re.search(condition_value, str(value)))
            except re.error:
                return False

        elif condition_type == "greater_than":
            try:
                return float(value) > float(condition_value)
            except (ValueError, TypeError):
                return False

        elif condition_type == "less_than":
            try:
                return float(value) < float(condition_value)
            except (ValueError, TypeError):
                return False

        elif condition_type == "starts_with":
            return str_value.startswith(str(condition_value).lower())

        elif condition_type == "ends_with":
            return str_value.endswith(str(condition_value).lower())

        return False

    @staticmethod
    def extract_value(data: Dict[str, Any], key_path: str) -> Any:
        """Extract value from nested dictionary using dot notation"""
        keys = key_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value

    def evaluate_filter(
        self, data: Dict[str, Any], filter_config: Dict[str, Any], event_type: str
    ) -> bool:
        """Evaluate if data matches filter conditions"""
        # Check if event type matches
        if "events" in filter_config:
            if event_type not in filter_config["events"]:
                return False

        # Check conditions
        conditions = filter_config.get("conditions", {})
        any_of_conditions = filter_config.get("any_of", [])

        if not conditions and not any_of_conditions:
            return True  # No conditions means always match

        # Special handling for file_content_contains
        if "file_content_contains" in conditions:
            if not self._check_file_content(data, conditions):
                return False
            # Remove from conditions so it's not processed again
            conditions = {
                k: v for k, v in conditions.items() if k != "file_content_contains"
            }

        # All conditions must be true (AND logic)
        for field, condition in conditions.items():
            # Extract value from data
            value = self.get_field_value(data, field)

            # Evaluate condition
            if isinstance(condition, dict):
                # Multiple condition types for same field
                for condition_type, condition_value in condition.items():
                    if not self.evaluate_condition(
                        value, condition_type, condition_value, context=data
                    ):
                        return False
            else:
                # Simple equality check
                if str(value).lower() != str(condition).lower():
                    return False

        # Handle any_of conditions (OR logic)
        if any_of_conditions:
            any_matched = False
            for any_condition in any_of_conditions:
                for field, condition in any_condition.items():
                    value = self.get_field_value(data, field)

                    if isinstance(condition, dict):
                        # Check all condition types for this field
                        all_match = True
                        for condition_type, condition_value in condition.items():
                            if not self.evaluate_condition(
                                value, condition_type, condition_value, context=data
                            ):
                                all_match = False
                                break
                        if all_match:
                            any_matched = True
                            break
                    else:
                        # Simple equality check
                        if str(value).lower() == str(condition).lower():
                            any_matched = True
                            break

                if any_matched:
                    break

            if not any_matched:
                return False

        return True

    def _check_file_content(
        self, data: Dict[str, Any], conditions: Dict[str, Any]
    ) -> bool:
        """Check if modified files contain specific content"""
        if not self.file_content_fetcher:
            print(
                "[FilterEngine] File content fetcher not configured, skipping file content check"
            )
            return False

        # Get file content search criteria
        file_content_condition = conditions.get("file_content_contains", {})
        if isinstance(file_content_condition, dict):
            search_strings = file_content_condition.get("contains")
            if isinstance(search_strings, str):
                search_strings = [search_strings]
        else:
            search_strings = [str(file_content_condition)]

        # Get modified files list
        modified_files = data.get("modified_files", [])
        if not modified_files:
            return False

        # Get repository and platform info
        platform = data.get("platform")
        repository = data.get("repository")
        ref = data.get("ref", "").replace("refs/heads/", "")  # Extract branch name

        if not platform or not repository:
            print("[FilterEngine] Missing platform or repository info")
            return False

        # Check each modified file
        for file_path in modified_files:
            try:
                content = self.file_content_fetcher.fetch_file_content(
                    platform=platform,
                    repository=repository,
                    file_path=file_path,
                    ref=ref,
                )

                if content:
                    # Check if any search string is in the content
                    for search_string in search_strings:
                        if search_string.lower() in content.lower():
                            print(
                                f"[FilterEngine] Found '{search_string}' in {file_path}"
                            )
                            return True
            except Exception as e:
                print(f"[FilterEngine] Error checking file {file_path}: {e}")
                continue

        return False

    @staticmethod
    def get_field_value(data: Dict[str, Any], field: str) -> Any:
        """Extract field value from normalized event data"""
        # Direct lookup in normalized data
        if field in data:
            return data[field]

        # Try to extract from raw_data if not in normalized
        # raw_data = data.get('raw_data', {})

        # Common field mappings that might still be needed
        field_mappings = {
            "repository_name": ["repository"],
            "repository_description": ["repository_description"],
            "issue_title": ["issue_title"],
            "issue_number": ["issue_number"],
            "issue_body": ["issue_body"],
            "pr_title": ["pr_title"],
            "pr_number": ["pr_number"],
            "pr_body": ["pr_body"],
            "pr_changes": ["pr_changes"],
            "workflow_name": ["workflow_name"],
            "conclusion": ["workflow_conclusion"],
            "environment": ["environment"],
            "state": ["deployment_state", "pr_state"],
            "labels": ["labels"],
            "target_branch": ["target_branch"],
            "source_branch": ["source_branch"],
            "ref": ["ref"],
            "status": ["workflow_status"],
            "user": ["sender", "pusher"],
            "project": ["repository"],
            "pipeline_id": ["pipeline_id"],
            "mr_iid": ["pr_number"],
            "mr_title": ["pr_title"],
            "modified_files": ["modified_files"],
            "commit_messages": ["commit_messages"],
        }

        # Try mapped fields
        if field in field_mappings:
            for mapped_field in field_mappings[field]:
                if mapped_field in data:
                    return data[mapped_field]

        return None

    @staticmethod
    def format_message(template: str, data: Dict[str, Any]) -> str:
        """Format message template with normalized data"""
        # Use normalized data fields directly
        fields = {
            "repository": data.get("repository", "N/A"),
            "repository_url": data.get("repository_url", ""),
            "repo": data.get("repository", "N/A"),
            "project": data.get("repository", "N/A"),  # Use same field for both
            "issue_number": data.get("issue_number", "N/A"),
            "issue_title": data.get("issue_title", "N/A"),
            "issue_url": data.get("issue_url", ""),
            "pr_number": data.get("pr_number", "N/A"),
            "pr_title": data.get("pr_title", "N/A"),
            "pr_url": data.get("pr_url", ""),
            "pr_changes": data.get("pr_changes", "N/A"),
            "workflow_name": data.get("workflow_name", "N/A"),
            "environment": data.get("environment", "N/A"),
            "state": data.get("deployment_state") or data.get("pr_state", "N/A"),
            "user": data.get("sender", "N/A"),
            "sender": data.get("sender", "N/A"),
            "status": data.get("workflow_status", "N/A"),
            "pipeline_id": data.get("pipeline_id", "N/A"),
            "mr_iid": data.get("pr_number", "N/A"),  # Use same as pr_number
            "mr_title": data.get("pr_title", "N/A"),  # Use same as pr_title
            "conclusion": data.get("workflow_conclusion", "N/A"),
            "compare_url": data.get("compare_url", ""),
            "commit_url": data.get("commit_url", ""),
            "ref": data.get("ref", "N/A"),
            "commits": data.get("commits", "N/A"),
            "pusher": data.get("pusher", "N/A"),
            "release_name": data.get("release_name", "N/A"),
            "release_tag": data.get("release_tag", "N/A"),
        }

        # Debug: log URL fields
        if data.get("event_type") == "push":
            print(
                f"[FilterEngine] Formatting message for push - compare_url: {fields.get('compare_url')}, commit_url: {fields.get('commit_url')}"
            )

        try:
            return template.format(**fields)
        except KeyError as e:
            print(f"[FilterEngine] Missing field in message template: {e}")
            return template
