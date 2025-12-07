import hmac
import hashlib
from flask import request
from helpers.handler.base import WebhookHandler
from helpers.normalizer import EventNormalizer


class GitHubWebhookHandler(WebhookHandler):
    """GitHub-specific webhook handler"""

    def register_endpoint(self):
        """Register the GitHub webhook endpoint"""

        @self.app.route(self.endpoint, methods=["POST"])
        def github_webhook():
            return self.handle_request()

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not signature:
            return False

        # GitHub sends signature as "sha256=<hash>"
        expected_signature = hmac.new(
            self.secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Extract the hash part after "sha256="
        if signature.startswith("sha256="):
            signature = signature[7:]
        elif signature.startswith("sha1="):
            # Fallback to sha1 if that's what's sent
            expected_signature = hmac.new(
                self.secret.encode(), payload, hashlib.sha1
            ).hexdigest()
            signature = signature[5:]

        return hmac.compare_digest(expected_signature, signature)

    def get_event_info(self) -> tuple[str, str]:
        """Extract event type and action from GitHub headers"""
        event_type = request.headers.get("X-Github-Event", "unknown")
        data = request.get_json()
        action = data.get("action")
        return event_type, action

    def get_signature_header(self) -> str:
        """Get GitHub signature from headers"""
        return request.headers.get("X-Hub-Signature-256") or request.headers.get(
            "X-Hub-Signature", ""
        )

    def normalize_data(self, data: dict, event_type: str) -> dict:
        """Normalize GitHub data to standard format"""
        return EventNormalizer.normalize_github(data, event_type)
