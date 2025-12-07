from helpers.notification.base import NotificationChannel
from typing import Dict, Any


class SlackNotification(NotificationChannel):
    """Slack notification channel"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel")  # Optional - webhook has default
        self.username = config.get("username")  # Optional - webhook has default

    def send(self, message: str, event_data: Dict[str, Any] = None):
        """Send notification to Slack"""
        import requests

        if not self.webhook_url:
            print("[Slack] No webhook URL configured")
            return

        # Build payload - all fields are optional (webhook has defaults)
        payload = {"text": message, "icon_emoji": ":bell:"}

        # Only add optional fields if explicitly provided
        if self.username:
            payload["username"] = self.username
        if self.channel:
            payload["channel"] = self.channel

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print(f"[Slack] Notification sent: {message}")
        except Exception as e:
            print(f"[Slack] Failed to send notification: {e}")
