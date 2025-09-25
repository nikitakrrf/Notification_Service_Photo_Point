from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class Channel(str, Enum):
    email = "email"
    sms = "sms"
    telegram = "telegram"


class UserContact(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None  # E.164 format (e.g., +15551234567)
    telegram_chat_id: Optional[str] = None  # numeric chat_id (preferred)


class NotificationRequest(BaseModel):
    user_id: str = Field(..., description="Your internal user identifier")
    contacts: UserContact
    subject: Optional[str] = Field(None, description="Subject for email (optional)")
    message: str
    channels_order: List[Channel] = Field(
        default_factory=lambda: [Channel.telegram, Channel.email, Channel.sms],
        description="Order of channels to try for delivery",
    )
    per_channel_max_attempts: int = Field(1, ge=1, le=5, description="Retries per channel before falling back")


class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    delivered_via: Optional[Channel] = None