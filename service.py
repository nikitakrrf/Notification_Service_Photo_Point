import logging
from typing import Iterable

from models import Channel, UserContact
from providers import BaseProvider, EmailProvider, SMSProvider, TelegramProvider, ProviderNotConfigured
from storage import get_session, Notification, DeliveryAttempt

log = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, providers: dict[Channel, BaseProvider]):
        self.providers = providers

    def _iter_providers(self, order: Iterable[Channel]) -> Iterable[BaseProvider]:
        for ch in order:
            p = self.providers.get(ch)
            if p is not None:
                yield p

    def send_with_fallback(
        self,
        *,
        user_id: str,
        contacts: UserContact,
        subject: str | None,
        message: str,
        channels_order: list[Channel],
        per_channel_max_attempts: int = 1,
    ) -> Notification:
        session = get_session()
        notif = Notification(user_id=user_id, subject=subject, message=message, status="in_progress")
        session.add(notif)
        session.commit()
        session.refresh(notif)

        last_error: str | None = None
        delivered_via: Channel | None = None

        for provider in self._iter_providers(channels_order):
            for attempt in range(1, per_channel_max_attempts + 1):
                try:
                    log.info("Trying channel=%s attempt=%s for notification=%s", provider.channel, attempt, notif.id)
                    provider.send(contacts, subject, message)
                    session.add(
                        DeliveryAttempt(
                            notification_id=notif.id, channel=provider.channel, attempt_no=attempt, success=1
                        )
                    )
                    delivered_via = provider.channel
                    notif.status = "delivered"
                    notif.delivered_via = delivered_via
                    session.commit()
                    return notif
                except ProviderNotConfigured as e:
                    log.warning("Provider %s not configured: %s", provider.channel, e)
                    session.add(
                        DeliveryAttempt(
                            notification_id=notif.id, channel=provider.channel, attempt_no=attempt, success=0, error=str(e)
                        )
                    )
                    session.commit()
                    break  # go to next channel
                except Exception as e:
                    last_error = str(e)
                    log.error("Delivery via %s failed on attempt %s: %s", provider.channel, attempt, e)
                    session.add(
                        DeliveryAttempt(
                            notification_id=notif.id, channel=provider.channel, attempt_no=attempt, success=0, error=str(e)
                        )
                    )
                    session.commit()
                    continue

        notif.status = "failed"
        session.commit()
        if last_error:
            log.error("Notification %s failed: %s", notif.id, last_error)
        return notif

