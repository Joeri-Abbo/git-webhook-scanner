import os
from pathlib import Path

import yaml
from flask import Flask
from asgiref.wsgi import WsgiToAsgi
from helpers.handler.github import GitHubWebhookHandler
from helpers.handler.gitlab import GitLabWebhookHandler
from dotenv import load_dotenv
from helpers.notification.factory import NotificationFactory
from helpers.file_content_fetcher import FileContentFetcher

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize file content fetcher
file_fetcher = FileContentFetcher()
github_status = "✓" if file_fetcher.github_client else "✗"
if file_fetcher.github_org_tokens:
    org_names = ", ".join(file_fetcher.github_org_tokens.keys())
    github_status += f" (org-specific: {org_names})"
gitlab_status = "✓" if file_fetcher.gitlab_client else "✗"
print(
    f"File content fetcher initialized (GitHub: {github_status}, GitLab: {gitlab_status})"
)

# Load configuration from YAML with fallback to example
primary_config_path = Path(os.getenv("CONFIG_PATH", "config.yaml"))
fallback_config_path = Path("config.example.yaml")
config = None

for candidate in [primary_config_path, fallback_config_path]:
    if candidate.exists():
        with candidate.open("r") as f:
            config = yaml.safe_load(f) or {}
        if candidate == fallback_config_path and candidate != primary_config_path:
            print(
                f"Using fallback configuration from {fallback_config_path}; create {primary_config_path} to override."
            )
        break

if config is None:
    raise FileNotFoundError(
        f"No configuration file found. Looked for {primary_config_path} and {fallback_config_path}."
    )

# Set up notification channel from environment variables
channel_type = os.getenv("NOTIFICATION_CHANNEL", "slack")

if channel_type == "slack":
    # Channel and username are optional - webhook URL has defaults configured
    channel_config = {
        "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
    }
elif channel_type == "email":
    to_addresses = os.getenv("EMAIL_TO_ADDRESSES", "").split(",")
    to_addresses = [addr.strip() for addr in to_addresses if addr.strip()]
    channel_config = {
        "smtp_host": os.getenv("EMAIL_SMTP_HOST"),
        "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", 587)),
        "smtp_user": os.getenv("EMAIL_SMTP_USER"),
        "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD"),
        "from_address": os.getenv("EMAIL_FROM_ADDRESS"),
        "to_addresses": to_addresses,
    }
else:
    channel_config = {}

try:
    notification_manager = NotificationFactory.create(channel_type, channel_config)
    print(f"Notification channel: {channel_type}")
except Exception as e:
    print(f"Failed to initialize notification channel: {e}")
    notification_manager = None


def filter_applies_to_platform(filter_config, platform):
    """Check if a filter applies to the given platform"""
    filter_platform = filter_config.get("platform", [])

    # If no platform specified, apply to all
    if not filter_platform:
        return True

    # If platform is a string, convert to list
    if isinstance(filter_platform, str):
        filter_platform = [filter_platform]

    return platform in filter_platform


# Initialize GitHub webhook handler
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "replace-me")
all_filters = config.get("filters", [])
# Filter for GitHub platform
github_filters = [f for f in all_filters if filter_applies_to_platform(f, "github")]
github_handler = GitHubWebhookHandler(
    app=app,
    endpoint="/github/webhook",
    secret=GITHUB_WEBHOOK_SECRET,
    notification_manager=notification_manager,
    filters=github_filters,
    file_content_fetcher=file_fetcher,
)

# Initialize GitLab webhook handler
GITLAB_WEBHOOK_TOKEN = os.getenv("GITLAB_WEBHOOK_TOKEN", "replace-me")
# Filter for GitLab platform
gitlab_filters = [f for f in all_filters if filter_applies_to_platform(f, "gitlab")]
gitlab_handler = GitLabWebhookHandler(
    app=app,
    endpoint="/gitlab/webhook",
    secret=GITLAB_WEBHOOK_TOKEN,
    notification_manager=notification_manager,
    filters=gitlab_filters,
    file_content_fetcher=file_fetcher,
)

print(f"Total filters: {len(all_filters)}")
print(f"GitHub filters: {len(github_filters)}")
print(f"GitLab filters: {len(gitlab_filters)}")


# ============================================
# GitHub Event Handlers
# ============================================


@github_handler.register_handler()
def on_github_any_event(data):
    """Catch-all handler for GitHub events"""
    if not data:
        print("[GitHub ANY] No data received")
        return

    repo = data.get("repository", "N/A")
    action = data.get("action", "N/A")
    event_type = data.get("event_type", "N/A")
    print(f"[GitHub ANY] event={event_type} repo={repo} action={action}")


@github_handler.register_handler("push")
def on_github_push(data):
    # Use normalized data
    repo = data.get("repository")
    ref = data.get("ref")
    pusher = data.get("pusher")
    commits = data.get("commits", 0)
    print(f"[GitHub push] repo={repo} ref={ref} by={pusher} commits={commits}")


@github_handler.register_handler("pull_request")
def on_github_pull_request(data):
    # Use normalized data
    action = data.get("action", "unknown")
    repo = data.get("repository")
    pr_number = data.get("pr_number")
    pr_title = data.get("pr_title")
    sender = data.get("sender")
    print(
        f"[GitHub pull_request] action={action} repo={repo} pr=#{pr_number} title='{pr_title}' by={sender}"
    )


@github_handler.register_handler("issues")
def on_github_issues(data):
    # Use normalized data
    action = data.get("action", "unknown")
    repo = data.get("repository")
    issue_number = data.get("issue_number")
    issue_title = data.get("issue_title")
    print(
        f"[GitHub issues] action={action} repo={repo} issue=#{issue_number} title='{issue_title}'"
    )


@github_handler.register_handler("release")
def on_github_release(data):
    # Use normalized data
    action = data.get("action", "unknown")
    repo = data.get("repository")
    release_name = data.get("release_name")
    tag_name = data.get("release_tag")
    print(
        f"[GitHub release] action={action} repo={repo} release='{release_name}' tag={tag_name}"
    )


@github_handler.register_handler("workflow_job")
def on_github_workflow_job(data):
    # Use normalized data
    action = data.get("action", "unknown")
    repo = data.get("repository")
    workflow_name = data.get("workflow_name")
    status = data.get("workflow_status")
    conclusion = data.get("workflow_conclusion")
    print(
        f"[GitHub workflow_job] action={action} repo={repo} workflow='{workflow_name}' status={status} conclusion={conclusion}"
    )


# ============================================
# GitLab Event Handlers
# ============================================


@gitlab_handler.register_handler()
def on_gitlab_any_event(data):
    """Catch-all handler for GitLab events"""
    project = data.get("project", {}).get("path_with_namespace", "N/A")
    event_name = data.get("event_name", "N/A")
    print(f"[GitLab ANY] project={project} event={event_name}")


@gitlab_handler.register_handler("push")
def on_gitlab_push(data):
    project = data["project"]["path_with_namespace"]
    ref = data["ref"]
    user_name = data["user_name"]
    total_commits = data["total_commits_count"]
    print(
        f"[GitLab push] project={project} ref={ref} by={user_name} commits={total_commits}"
    )


@gitlab_handler.register_handler("merge_request")
def on_gitlab_merge_request(data):
    action = data.get("object_attributes", {}).get("action", "unknown")
    project = data["project"]["path_with_namespace"]
    mr_iid = data["object_attributes"]["iid"]
    mr_title = data["object_attributes"]["title"]
    user = data.get("user", {}).get("username", "N/A")
    print(
        f"[GitLab merge_request] action={action} project={project} mr=!{mr_iid} title='{mr_title}' by={user}"
    )


@gitlab_handler.register_handler("issue")
def on_gitlab_issue(data):
    action = data.get("object_attributes", {}).get("action", "unknown")
    project = data["project"]["path_with_namespace"]
    issue_iid = data["object_attributes"]["iid"]
    issue_title = data["object_attributes"]["title"]
    user = data.get("user", {}).get("username", "N/A")
    print(
        f"[GitLab issue] action={action} project={project} issue=#{issue_iid} title='{issue_title}' by={user}"
    )


@gitlab_handler.register_handler("pipeline")
def on_gitlab_pipeline(data):
    project = data["project"]["path_with_namespace"]
    pipeline_id = data["object_attributes"]["id"]
    status = data["object_attributes"]["status"]
    ref = data["object_attributes"]["ref"]
    print(
        f"[GitLab pipeline] project={project} pipeline=#{pipeline_id} ref={ref} status={status}"
    )


@gitlab_handler.register_handler("job")
def on_gitlab_job(data):
    project = data["project"]["path_with_namespace"]
    job_name = data["build_name"]
    status = data["build_status"]
    stage = data["build_stage"]
    print(
        f"[GitLab job] project={project} job='{job_name}' stage={stage} status={status}"
    )


@gitlab_handler.register_handler("tag_push")
def on_gitlab_tag_push(data):
    project = data["project"]["path_with_namespace"]
    ref = data["ref"]
    user_name = data["user_name"]
    print(f"[GitLab tag_push] project={project} tag={ref} by={user_name}")


@gitlab_handler.register_handler("release")
def on_gitlab_release(data):
    action = data.get("action", "unknown")
    project = data["project"]["path_with_namespace"]
    tag = data.get("tag", "N/A")
    name = data.get("name", "N/A")
    print(
        f"[GitLab release] action={action} project={project} release='{name}' tag={tag}"
    )


# ============================================
# Health Check & Test Endpoints
# ============================================


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/test/notification")
def test_notification():
    """Test endpoint to verify notification integration"""
    if not notification_manager:
        return {
            "status": "error",
            "message": "Notification manager not configured",
        }, 500

    try:
        test_message = "🧪 Test notification from webhook handler"
        test_data = {
            "repository": "test/repo",
            "event_type": "test",
            "platform": "test",
        }

        notification_manager.send(test_message, test_data)

        return {
            "status": "success",
            "message": "Test notification sent!",
            "channel": channel_type,
            "details": "Check your notification channel for the test message",
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send notification: {str(e)}",
        }, 500


# Wrap Flask app for ASGI compatibility with Uvicorn
asgi_app = WsgiToAsgi(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
