from helpers.notification.base import NotificationChannel
from helpers.notification.slack import SlackNotification
from helpers.notification.email import EmailNotification
from typing import Dict, Any


class NotificationFactory:
    """Factory for creating notification channels"""

    @staticmethod
    def create(channel_type: str, config: Dict[str, Any]) -> NotificationChannel:
        """Create a notification channel based on type"""
        channels = {"slack": SlackNotification, "email": EmailNotification}

        channel_class = channels.get(channel_type.lower())
        if not channel_class:
            raise ValueError(f"Unknown notification channel: {channel_type}")

        return channel_class(config)
