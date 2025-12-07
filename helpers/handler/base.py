from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List
from flask import Flask, request


class WebhookHandler(ABC):
    """Base class for webhook handlers"""

    def __init__(
        self,
        app: Flask,
        endpoint: str,
        secret: str,
        notification_manager=None,
        filters: List[Dict] = None,
        file_content_fetcher=None,
    ):
        self.app = app
        self.endpoint = endpoint
        self.secret = secret
        self.event_handlers: Dict[str, list] = {}
        self.notification_manager = notification_manager
        self.filters = filters or []
        self.file_content_fetcher = file_content_fetcher

        # Register the webhook endpoint
        self.register_endpoint()

    @abstractmethod
    def register_endpoint(self):
        """Register the webhook endpoint with Flask"""
        pass

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the webhook signature"""
        pass

    @abstractmethod
    def get_event_info(self) -> tuple[str, str]:
        """Extract event type and action from the request"""
        pass

    @abstractmethod
    def normalize_data(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Normalize webhook data to standard format"""
        pass

    def register_handler(self, event_type: str = None):
        """Decorator to register event handlers"""

        def decorator(func: Callable):
            if event_type is None:
                # Catch-all handler
                event_key = "__all__"
            else:
                event_key = event_type

            if event_key not in self.event_handlers:
                self.event_handlers[event_key] = []

            self.event_handlers[event_key].append(func)
            return func

        return decorator

    def process_event(self, data: Dict[str, Any], event_type: str, action: str = None):
        """Process the webhook event by calling registered handlers"""
        try:
            # Call specific event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(data)

            # Call catch-all handlers
            if "__all__" in self.event_handlers:
                for handler in self.event_handlers["__all__"]:
                    handler(data)
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error in event handler: {e}")
            import traceback

            traceback.print_exc()

        # Check filters and send notifications
        try:
            if self.notification_manager and self.filters:
                self.check_and_notify(data, event_type, action)
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error in filter/notification: {e}")
            import traceback

            traceback.print_exc()

    def check_and_notify(
        self, data: Dict[str, Any], event_type: str, action: str = None
    ):
        """Check filters and send notifications if conditions match"""
        from helpers.filter_engine import FilterEngine

        # Initialize filter engine with file content fetcher
        filter_engine = FilterEngine(file_content_fetcher=self.file_content_fetcher)

        for filter_config in self.filters:
            if filter_engine.evaluate_filter(data, filter_config, event_type):
                if filter_config.get("notify", False):
                    message_template = filter_config.get(
                        "message", "Event triggered: {repository}"
                    )
                    message = FilterEngine.format_message(message_template, data)
                    filter_name = filter_config.get("name", "Unknown")

                    print(f"[Filter Matched] {filter_name}: {message}")

                    # Send notification
                    try:
                        self.notification_manager.send(message, data)
                    except Exception as e:
                        print(
                            f"[Filter] Failed to send notification for '{filter_name}': {e}"
                        )
                        import traceback

                        traceback.print_exc()

    def handle_request(self):
        """Main request handler"""
        try:
            # Get the raw payload
            payload = request.data

            # Verify signature
            signature = self.get_signature_header()
            if not self.verify_signature(payload, signature):
                print(f"[{self.__class__.__name__}] Invalid signature")
                return {"error": "Invalid signature"}, 401

            # Parse JSON data
            data = request.get_json()

            # Get event info
            event_type, action = self.get_event_info()

            # Normalize data to standard format
            normalized_data = self.normalize_data(data, event_type)

            # Log request
            print(
                f"[{self.__class__.__name__}] {event_type}"
                + (f".{action}" if action else "")
            )

            # Process the event with normalized data
            self.process_event(normalized_data, event_type, action)

            return "", 204

        except Exception as e:
            print(f"[{self.__class__.__name__}] Error: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}, 500

    @abstractmethod
    def get_signature_header(self) -> str:
        """Get the signature from request headers"""
        pass
