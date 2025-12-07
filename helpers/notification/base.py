from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationChannel(ABC):
    """Base class for notification channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def send(self, message: str, event_data: Dict[str, Any] = None):
        """Send a notification"""
        pass
