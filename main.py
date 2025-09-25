import logging
from fastapi import FastAPI, HTTPException
from models import NotificationRequest, NotificationResponse, Channel
from config import load_config
from storage import init_engine, get_session, Notification
from providers import EmailProvider, SMSProvider, TelegramProvider
from service import NotificationService

app = FastAPI(title="Notification Service", version="1.0.0")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

_cfg = load_config()
init_engine(_cfg.database_url)

_providers = {
    Channel.email: EmailProvider(_cfg),
    Channel.sms: SMSProvider(_cfg),
    Channel.telegram: TelegramProvider(_cfg),
}

_service = NotificationService(_providers)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/notify", response_model=NotificationResponse)
def create_notification(req: NotificationRequest):
    notif = _service.send_with_fallback(
        user_id=req.user_id,
        contacts=req.contacts,
        subject=req.subject,
        message=req.message,
        channels_order=req.channels_order,
        per_channel_max_attempts=req.per_channel_max_attempts,
    )

    if notif.status == "failed":
        raise HTTPException(status_code=502, detail="All channels failed to deliver the message")

    return NotificationResponse(notification_id=notif.id, status=notif.status, delivered_via=notif.delivered_via)


@app.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: str):
    session = get_session()
    notif = session.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse(
        notification_id=notif.id, status=notif.status, delivered_via=notif.delivered_via
    )

