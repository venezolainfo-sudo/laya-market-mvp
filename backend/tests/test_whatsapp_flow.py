import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.db import SessionLocal
from app.main import app
from app.whatsapp_models import WhatsAppEvent

client = TestClient(app)


def test_whatsapp_webhook_verification():
    original = settings.whatsapp_verify_token
    settings.whatsapp_verify_token = "ci-verify-token"
    try:
        response = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "ci-verify-token",
                "hub.challenge": "123456",
            },
        )
        assert response.status_code == 200
        assert response.text == "123456"

        rejected = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong",
                "hub.challenge": "123456",
            },
        )
        assert rejected.status_code == 403
    finally:
        settings.whatsapp_verify_token = original


def test_whatsapp_incoming_message_is_persisted_and_deduplicated():
    message_id = f"wamid.ci-{uuid.uuid4()}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-ci",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15556063878",
                                "phone_number_id": "test-phone-id",
                            },
                            "messages": [
                                {
                                    "from": "5492610000000",
                                    "id": message_id,
                                    "timestamp": "1789230000",
                                    "text": {"body": "Prueba webhook LAYA"},
                                    "type": "text",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    first = client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["stored"] == 1
    assert first.json()["duplicates"] == 0

    second = client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert second.status_code == 200, second.text
    assert second.json()["stored"] == 0
    assert second.json()["duplicates"] == 1

    db = SessionLocal()
    try:
        event = db.scalar(select(WhatsAppEvent).where(WhatsAppEvent.external_id == message_id))
        assert event is not None
        assert event.event_type == "message"
        assert event.status == "received"
        assert event.message_type == "text"
        assert event.body == "Prueba webhook LAYA"
    finally:
        db.close()


def test_whatsapp_delivery_status_is_persisted():
    message_id = f"wamid.status-{uuid.uuid4()}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-ci",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": "test-phone-id"},
                            "statuses": [
                                {
                                    "id": message_id,
                                    "status": "delivered",
                                    "recipient_id": "5492610000000",
                                    "timestamp": "1789230001",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    response = client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["stored"] == 1

    db = SessionLocal()
    try:
        event = db.scalar(
            select(WhatsAppEvent).where(
                WhatsAppEvent.external_id == message_id,
                WhatsAppEvent.event_type == "status:delivered",
            )
        )
        assert event is not None
        assert event.status == "delivered"
    finally:
        db.close()
