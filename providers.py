import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth

from config import AppConfig
from models import Channel, UserContact


log = logging.getLogger(__name__)


class ProviderNotConfigured(RuntimeError):
    pass


class BaseProvider:
    channel: Channel

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def send(self, contacts: UserContact, subject: Optional[str], message: str) -> None:
        raise NotImplementedError


class EmailProvider(BaseProvider):
    channel = Channel.email

    def send(self, contacts: UserContact, subject: Optional[str], message: str) -> None:
        if not self.cfg.smtp.host or not self.cfg.smtp.username or not self.cfg.smtp.password:
            raise ProviderNotConfigured("SMTP not configured")
        if not contacts.email:
            raise ValueError("Recipient email is missing")

        mime = MIMEText(message, _charset="utf-8")
        mime["Subject"] = subject or "Notification"
        mime["From"] = self.cfg.smtp.username
        mime["To"] = contacts.email

        log.debug("Connecting SMTP %s:%s TLS=%s", self.cfg.smtp.host, self.cfg.smtp.port, self.cfg.smtp.use_tls)
        server = smtplib.SMTP(self.cfg.smtp.host, self.cfg.smtp.port, timeout=20)
        try:
            if self.cfg.smtp.use_tls:
                server.starttls()
            server.login(self.cfg.smtp.username, self.cfg.smtp.password)
            server.sendmail(self.cfg.smtp.username, [contacts.email], mime.as_string())
        finally:
            server.quit()


class SMSProvider(BaseProvider):
    channel = Channel.sms

    def send(self, contacts: UserContact, subject: Optional[str], message: str) -> None:
        sid = self.cfg.twilio.account_sid
        token = self.cfg.twilio.auth_token
        from_number = self.cfg.twilio.from_number
        if not sid or not token or not from_number:
            raise ProviderNotConfigured("Twilio not configured")
        if not contacts.phone:
            raise ValueError("Recipient phone is missing")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = {
            "From": from_number,
            "To": contacts.phone,
            "Body": message if len(message) <= 1600 else message[:1597] + "...",
        }
        resp = requests.post(url, data=data, auth=HTTPBasicAuth(sid, token), timeout=20)
        if resp.status_code >= 300:
            raise RuntimeError(f"Twilio error: {resp.status_code} {resp.text}")


class TelegramProvider(BaseProvider):
    channel = Channel.telegram

    def send(self, contacts: UserContact, subject: Optional[str], message: str) -> None:
        token = self.cfg.telegram.bot_token
        if not token:
            raise ProviderNotConfigured("Telegram bot token not configured")
        chat_id = contacts.telegram_chat_id
        if not chat_id:
            raise ValueError("Telegram chat_id is missing")

        text = f"{('*' + subject + '*') if subject else ''}{message}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code >= 300:
            raise RuntimeError(f"Telegram error: {resp.status_code} {resp.text}")

