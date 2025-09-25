# Notification Service — Email/SMS/Telegram with Fallback

## 1. What it does
- Exposes `POST /notify` to send a message to a user.
- Tries channels in given order (default: Telegram → Email → SMS).
- If a channel is misconfigured or fails, it moves to the next one.
- Persists status + attempts in SQLite (`notifications.db`) or mounted volume in Docker.

## 2. Quick start
### Local (without Docker)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### With Docker
```bash
# Build & run container
mkdir -p data
sudo docker compose up --build -d

# Open docs
http://127.0.0.1:8000/docs
```

## 3. Example request
```json
{
  "user_id": "u-42",
  "contacts": {
    "email": "user@example.com",
    "phone": "+15551234567",
    "telegram_chat_id": "123456789"
  },
  "subject": "Hello",
  "message": "Test message",
  "channels_order": ["telegram", "email", "sms"],
  "per_channel_max_attempts": 1
}
```

## 4. Notes
- **Telegram**: supply `telegram_chat_id` (numeric). The user must have started a chat with your bot.
- **Email**: uses basic SMTP with TLS.
- **SMS**: uses Twilio REST API via `requests`.
- **Fallback**: provider not configured ⇒ skipped; runtime error ⇒ recorded and fallback.
- **Idempotency**: each call creates a record.
- **Extending**: add providers by implementing `BaseProvider` and registering in `_providers`.
