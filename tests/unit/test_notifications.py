"""Unit tests for notification system"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from helpers.notification.factory import NotificationFactory
from helpers.notification.slack import SlackNotification
from helpers.notification.email import EmailNotification


class TestNotificationFactory:
    """Test NotificationFactory"""

    def test_create_slack_notification(self):
        """Test creating Slack notification channel"""
        config = {"webhook_url": "https://hooks.slack.com/test"}
        notification = NotificationFactory.create("slack", config)
        assert isinstance(notification, SlackNotification)

    def test_create_email_notification(self):
        """Test creating Email notification channel"""
        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_address": "sender@example.com",
            "to_addresses": ["recipient@example.com"],
        }
        notification = NotificationFactory.create("email", config)
        assert isinstance(notification, EmailNotification)

    def test_create_invalid_channel(self):
        """Test creating invalid notification channel"""
        with pytest.raises(ValueError):
            NotificationFactory.create("invalid", {})


class TestSlackNotification:
    """Test SlackNotification"""

    @patch("requests.post")
    def test_send_notification_success(self, mock_post):
        """Test successful Slack notification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        config = {"webhook_url": "https://hooks.slack.com/test"}
        slack = SlackNotification(config)

        event_data = {"repository": "org/repo", "issue_number": 42}
        slack.send("Test message", event_data)

        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://hooks.slack.com/test"
        assert call_args[1]["json"]["text"] == "Test message"

    @patch("requests.post")
    def test_send_notification_with_channel(self, mock_post):
        """Test Slack notification with custom channel"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        config = {
            "webhook_url": "https://hooks.slack.com/test",
            "channel": "#alerts",
            "username": "WebhookBot",
        }
        slack = SlackNotification(config)

        slack.send("Test message")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["channel"] == "#alerts"
        assert payload["username"] == "WebhookBot"

    @patch("requests.post")
    def test_send_notification_failure(self, mock_post):
        """Test Slack notification failure handling"""
        mock_post.side_effect = Exception("Connection error")

        config = {"webhook_url": "https://hooks.slack.com/test"}
        slack = SlackNotification(config)

        # Should not raise exception
        slack.send("Test message")

    def test_send_without_webhook_url(self):
        """Test sending without webhook URL"""
        config = {}
        slack = SlackNotification(config)

        # Should not raise exception
        slack.send("Test message")


class TestEmailNotification:
    """Test EmailNotification"""

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class):
        """Test successful email notification"""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_address": "sender@example.com",
            "to_addresses": ["recipient@example.com"],
        }
        email = EmailNotification(config)

        event_data = {"repository": "org/repo"}
        email.send("Test message", event_data)

        # Verify SMTP methods were called
        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password")
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_multiple_recipients(self, mock_smtp_class):
        """Test email to multiple recipients"""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_address": "sender@example.com",
            "to_addresses": ["recipient1@example.com", "recipient2@example.com"],
        }
        email = EmailNotification(config)

        email.send("Test message")

        # Verify email was sent
        mock_server.send_message.assert_called_once()
        sent_message = mock_server.send_message.call_args[0][0]
        assert "recipient1@example.com" in sent_message["To"]
        assert "recipient2@example.com" in sent_message["To"]

    @patch("smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure handling"""
        mock_smtp.side_effect = Exception("SMTP connection error")

        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_address": "sender@example.com",
            "to_addresses": ["recipient@example.com"],
        }
        email = EmailNotification(config)

        # Should not raise exception
        email.send("Test message")

    def test_send_without_config(self):
        """Test sending without proper configuration"""
        config = {"smtp_host": "smtp.example.com"}  # Missing required fields
        email = EmailNotification(config)

        # Should not raise exception
        email.send("Test message")
