from flask import request
from helpers.handler.base import WebhookHandler
from helpers.normalizer import EventNormalizer


class GitLabWebhookHandler(WebhookHandler):
    """GitLab-specific webhook handler"""

    def register_endpoint(self):
        """Register the GitLab webhook endpoint"""

        @self.app.route(self.endpoint, methods=["POST"])
        def gitlab_webhook():
            return self.handle_request()

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitLab webhook token"""
        # GitLab uses a simple token instead of HMAC
        # The token is sent in X-Gitlab-Token header
        return signature == self.secret

    def get_event_info(self) -> tuple[str, str]:
        """Extract event type and action from GitLab headers"""
        # GitLab sends event type in X-Gitlab-Event header
        event_type = request.headers.get("X-Gitlab-Event", "unknown")

        # Normalize event type (remove " Hook" suffix if present)
        if event_type.endswith(" Hook"):
            event_type = event_type[:-5].lower().replace(" ", "_")

        # Get action from payload if available
        data = request.get_json()
        action = data.get("object_attributes", {}).get("action")

        return event_type, action

    def get_signature_header(self) -> str:
        """Get GitLab token from headers"""
        return request.headers.get("X-Gitlab-Token", "")

    def normalize_data(self, data: dict, event_type: str) -> dict:
        """Normalize GitLab data to standard format"""
        return EventNormalizer.normalize_gitlab(data, event_type)
