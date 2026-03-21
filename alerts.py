"""
alerts.py — Multi-channel notification dispatch for ISMAP.

Changes from original:
  - send_alert() now accepts an `extra` kwarg so the caller-supplied rich message
    is actually used (fixes the silent signature mismatch with app.py)
  - Bare except clauses replaced with typed Exception catches
  - print() replaced with logging
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

import requests

logger = logging.getLogger(__name__)


def send_slack_alert(message: str, webhook_url: str) -> None:
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={"text": message}, timeout=5)
    except Exception as exc:
        logger.error("Slack alert failed: %s", exc)


def send_telegram_alert(message: str, bot_token: str, chat_id: str) -> None:
    if not bot_token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
    except Exception as exc:
        logger.error("Telegram alert failed: %s", exc)


def send_email_alert(
    subject: str,
    body: str,
    smtp_server: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipient: str,
) -> None:
    if not sender or not password or not recipient:
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
    except Exception as exc:
        logger.error("Email alert failed: %s", exc)


def send_alert(
    change_type: str,
    subdomain: str,
    domain: str,
    alert_config: dict,
    *,
    extra: str | None = None,
) -> None:
    """
    Dispatch an alert to all configured channels.

    Parameters
    ----------
    change_type : str
        Human-readable label, e.g. "New Subdomain".
    subdomain : str
        The subdomain that changed.
    domain : str
        The parent domain name.
    alert_config : dict
        Channel configuration (webhooks, tokens, SMTP settings).
    extra : str, optional
        Pre-formatted message body. Overrides the default if supplied.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = extra or (
        f"ISMAP Alert: {change_type}\n\n"
        f"Domain: {domain}\nSubdomain: {subdomain}\nTime: {timestamp}"
    )

    if alert_config.get("slack_webhook"):
        send_slack_alert(message, alert_config["slack_webhook"])

    if alert_config.get("telegram_bot_token") and alert_config.get("telegram_chat_id"):
        send_telegram_alert(
            message,
            alert_config["telegram_bot_token"],
            alert_config["telegram_chat_id"],
        )

    if alert_config.get("email"):
        send_email_alert(
            subject=f"ISMAP Alert: {change_type}",
            body=message,
            smtp_server=alert_config.get("smtp_server", "smtp.gmail.com"),
            smtp_port=alert_config.get("smtp_port", 587),
            sender=alert_config["email"],
            password=alert_config.get("email_password", ""),
            recipient=alert_config["email"],
        )
