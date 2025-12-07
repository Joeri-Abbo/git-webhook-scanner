from helpers.notification.base import NotificationChannel
from typing import Dict, Any


class EmailNotification(NotificationChannel):
    """Email notification channel"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user")
        self.smtp_password = config.get("smtp_password")
        self.from_address = config.get("from_address")
        self.to_addresses = config.get("to_addresses", [])

    def send(self, message: str, event_data: Dict[str, Any] = None):
        """Send notification via email"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not all(
            [self.smtp_host, self.smtp_user, self.smtp_password, self.from_address]
        ):
            print("[Email] Incomplete email configuration")
            return

        if not self.to_addresses:
            print("[Email] No recipients configured")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = ", ".join(self.to_addresses)
            msg["Subject"] = "Webhook Alert"

            body = message
            if event_data:
                body += f"\n\nEvent Data:\n{event_data}"

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print(
                f"[Email] Notification sent to {len(self.to_addresses)} recipients: {message}"
            )
        except Exception as e:
            print(f"[Email] Failed to send notification: {e}")
