from typing import Dict, Any


class EventNormalizer:
    """Normalize webhook events from different platforms into a standard format"""

    @staticmethod
    def normalize_github(data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Normalize GitHub webhook data to standard format"""
        normalized = {
            "platform": "github",
            "event_type": event_type,
            "action": data.get("action"),
            "repository": data.get("repository", {}).get("full_name"),
            "repository_description": data.get("repository", {}).get("description"),
            "repository_url": data.get("repository", {}).get("html_url"),
            "sender": data.get("sender", {}).get("login"),
            "raw_data": data,
        }

        # Add issue-specific fields
        if "issue" in data:
            normalized.update(
                {
                    "issue_number": data["issue"].get("number"),
                    "issue_title": data["issue"].get("title"),
                    "issue_body": data["issue"].get("body"),
                    "issue_url": data["issue"].get("html_url"),
                    "labels": [
                        label.get("name") for label in data["issue"].get("labels", [])
                    ],
                }
            )

        # Add pull request-specific fields
        if "pull_request" in data:
            normalized.update(
                {
                    "pr_number": data["pull_request"].get("number"),
                    "pr_title": data["pull_request"].get("title"),
                    "pr_body": data["pull_request"].get("body"),
                    "pr_url": data["pull_request"].get("html_url"),
                    "pr_changes": data["pull_request"].get("changed_files"),
                    "pr_state": data["pull_request"].get("state"),
                    "target_branch": data["pull_request"].get("base", {}).get("ref"),
                    "source_branch": data["pull_request"].get("head", {}).get("ref"),
                    "labels": [
                        label.get("name")
                        for label in data["pull_request"].get("labels", [])
                    ],
                }
            )

        # Add workflow-specific fields
        if "workflow_job" in data:
            normalized.update(
                {
                    "workflow_name": data["workflow_job"].get("name"),
                    "workflow_status": data["workflow_job"].get("status"),
                    "workflow_conclusion": data["workflow_job"].get("conclusion"),
                }
            )

        if "workflow_run" in data:
            normalized.update(
                {
                    "workflow_name": data["workflow_run"].get("name"),
                    "workflow_status": data["workflow_run"].get("status"),
                    "workflow_conclusion": data["workflow_run"].get("conclusion"),
                }
            )

        # Add deployment-specific fields
        if "deployment" in data:
            normalized.update(
                {
                    "environment": data["deployment"].get("environment"),
                    "deployment_state": data.get("deployment_status", {}).get("state"),
                }
            )

        # Add push-specific fields
        if event_type == "push":
            # Collect all modified/added/removed files from commits
            modified_files = []
            for commit in data.get("commits", []):
                modified_files.extend(commit.get("added", []))
                modified_files.extend(commit.get("modified", []))
                modified_files.extend(commit.get("removed", []))

            # Get compare URL (shows diff between before and after)
            compare_url = data.get("compare")
            # Get the head commit URL - use html_url for browser-friendly link
            commits_list = data.get("commits", [])
            if commits_list:
                # Try html_url first, fallback to url
                head_commit_url = commits_list[-1].get("html_url") or commits_list[
                    -1
                ].get("url")
            else:
                head_commit_url = None

            print(
                f"[Normalizer] Push event - compare_url: {compare_url}, commit_url: {head_commit_url}"
            )

            normalized.update(
                {
                    "ref": data.get("ref"),
                    "commits": len(data.get("commits", [])),
                    "pusher": data.get("pusher", {}).get("name"),
                    "modified_files": modified_files,
                    "commit_messages": [
                        c.get("message", "") for c in data.get("commits", [])
                    ],
                    "compare_url": compare_url,
                    "commit_url": head_commit_url,
                }
            )

        # Add release-specific fields
        if "release" in data:
            normalized.update(
                {
                    "release_name": data["release"].get("name"),
                    "release_tag": data["release"].get("tag_name"),
                }
            )

        # Add create event-specific fields (branch/tag creation)
        if event_type == "create":
            normalized.update(
                {
                    "ref": data.get("ref"),
                    "ref_type": data.get("ref_type"),  # 'branch' or 'tag'
                    "master_branch": data.get("master_branch"),
                    "description": data.get("description"),
                    "pusher_type": data.get("pusher_type"),
                }
            )

        # Add delete event-specific fields (branch/tag deletion)
        if event_type == "delete":
            normalized.update(
                {
                    "ref": data.get("ref"),
                    "ref_type": data.get("ref_type"),  # 'branch' or 'tag'
                    "pusher_type": data.get("pusher_type"),
                }
            )

        return normalized

    @staticmethod
    def normalize_gitlab(data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Normalize GitLab webhook data to standard format"""
        object_attrs = data.get("object_attributes", {})

        normalized = {
            "platform": "gitlab",
            "event_type": event_type,
            "action": object_attrs.get("action"),
            "repository": data.get("project", {}).get("path_with_namespace"),
            "repository_description": data.get("project", {}).get("description"),
            "sender": data.get("user", {}).get("username") or data.get("user_name"),
            "raw_data": data,
        }

        # Add issue-specific fields (GitLab calls them issues too)
        if event_type == "issue":
            normalized.update(
                {
                    "issue_number": object_attrs.get("iid"),
                    "issue_title": object_attrs.get("title"),
                    "issue_body": object_attrs.get("description"),
                    "labels": [label.get("title") for label in data.get("labels", [])],
                }
            )

        # Add merge request-specific fields (map to PR fields for consistency)
        if event_type == "merge_request":
            normalized.update(
                {
                    "pr_number": object_attrs.get("iid"),
                    "pr_title": object_attrs.get("title"),
                    "pr_body": object_attrs.get("description"),
                    "pr_changes": object_attrs.get("changes_count"),
                    "pr_state": object_attrs.get("state"),
                    "target_branch": object_attrs.get("target_branch"),
                    "source_branch": object_attrs.get("source_branch"),
                    "labels": [label.get("title") for label in data.get("labels", [])],
                }
            )

        # Add pipeline-specific fields (map to workflow fields)
        if event_type == "pipeline":
            normalized.update(
                {
                    "workflow_name": data.get("project", {}).get("name"),
                    "workflow_status": object_attrs.get("status"),
                    "workflow_conclusion": object_attrs.get("status"),
                    "pipeline_id": object_attrs.get("id"),
                }
            )

        # Add job-specific fields
        if event_type == "job":
            normalized.update(
                {
                    "workflow_name": data.get("build_name"),
                    "workflow_status": data.get("build_status"),
                    "workflow_conclusion": data.get("build_status"),
                    "job_stage": data.get("build_stage"),
                }
            )

        # Add push-specific fields
        if event_type == "push":
            # Collect all modified/added/removed files from commits
            modified_files = []
            for commit in data.get("commits", []):
                modified_files.extend(commit.get("added", []))
                modified_files.extend(commit.get("modified", []))
                modified_files.extend(commit.get("removed", []))

            normalized.update(
                {
                    "ref": data.get("ref"),
                    "commits": data.get("total_commits_count"),
                    "pusher": data.get("user_name"),
                    "modified_files": modified_files,
                    "commit_messages": [
                        c.get("message", "") for c in data.get("commits", [])
                    ],
                }
            )

        # Add tag push fields
        if event_type == "tag_push":
            normalized.update({"ref": data.get("ref"), "tag": data.get("ref")})

        # Add release-specific fields
        if event_type == "release":
            normalized.update(
                {"release_name": data.get("name"), "release_tag": data.get("tag")}
            )

        return normalized
