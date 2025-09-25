import os
from dataclasses import dataclass


@dataclass
class SMTPConfig:
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    use_tls: bool = True


@dataclass
class TwilioConfig:
    account_sid: str | None = None
    auth_token: str | None = None
    from_number: str | None = None


@dataclass
class TelegramConfig:
    bot_token: str | None = None


@dataclass
class AppConfig:
    smtp: SMTPConfig
    twilio: TwilioConfig
    telegram: TelegramConfig
    database_url: str


def load_config() -> AppConfig:
    smtp = SMTPConfig(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASS"),
        use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"},
    )

    twilio = TwilioConfig(
        account_sid=os.getenv("TWILIO_SID"),
        auth_token=os.getenv("TWILIO_TOKEN"),
        from_number=os.getenv("TWILIO_FROM"),
    )

    telegram = TelegramConfig(bot_token=os.getenv("TELEGRAM_BOT_TOKEN"))

    database_url = os.getenv("DATABASE_URL", "sqlite:///./notifications.db")

    return AppConfig(smtp=smtp, twilio=twilio, telegram=telegram, database_url=database_url)

