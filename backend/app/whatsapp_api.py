import hashlib
import hmac
import json
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Role, User
from app.security import require
from app.whatsapp_models import WhatsAppEvent

router = APIRouter(prefix="/api/v1/webhooks/whatsapp", tags=["whatsapp-webhook"])
ops_router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


class WhatsAppSendTestIn(BaseModel):
    to: str = Field(min_length=7, max_length=30)
    mode: str = Field(default="template", pattern="^(template|text)$")
    text: str | None = Field(default=None, max_length=4096)
    template_name: str = Field(default="hello_world", min_length=1, max_length=512)
    language_code: str = Field(default="en_US", min_length=2, max_length=20)


def _normalize_phone(value: str) -> str:
    phone = "".join(ch for ch in value if ch.isdigit())
    if len(phone) < 7:
        raise HTTPException(status_code=422, detail="Número de WhatsApp inválido")
    return phone


def _verify_signature(raw_body: bytes, signature: str | None) -> None:
    if not settings.whatsapp_app_secret:
        return
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Falta firma de Meta")
    expected = "sha256=" + hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Firma de Meta inválida")


def _message_body(message: dict[str, Any]) -> str | None:
    kind = message.get("type")
    if kind == "text":
        return (message.get("text") or {}).get("body")
    if kind in {"image", "video", "document"}:
        return (message.get(kind) or {}).get("caption")
    if kind == "button":
        return (message.get("button") or {}).get("text")
    if kind == "interactive":
        interactive = message.get("interactive") or {}
        reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
        return reply.get("title") or reply.get("id")
    return None


def _event_exists(db: Session, external_id: str, event_type: str) -> bool:
    return db.scalar(
        select(WhatsAppEvent.id).where(
            WhatsAppEvent.external_id == external_id,
            WhatsAppEvent.event_type == event_type,
        )
    ) is not None


def _store_payload_events(db: Session, payload: dict[str, Any]) -> tuple[int, int]:
    inserted = 0
    duplicates = 0
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")
            display_number = metadata.get("display_phone_number")

            for message in value.get("messages", []):
                external_id = message.get("id")
                if not external_id:
                    continue
                event_type = "message"
                if _event_exists(db, external_id, event_type):
                    duplicates += 1
                    continue
                db.add(
                    WhatsAppEvent(
                        external_id=external_id,
                        event_type=event_type,
                        phone_number_id=phone_number_id,
                        from_number=message.get("from"),
                        to_number=display_number,
                        status="received",
                        message_type=message.get("type"),
                        body=_message_body(message),
                        raw_json=raw,
                    )
                )
                inserted += 1

            for status in value.get("statuses", []):
                external_id = status.get("id")
                status_name = status.get("status") or "unknown"
                if not external_id:
                    continue
                event_type = f"status:{status_name}"
                if _event_exists(db, external_id, event_type):
                    duplicates += 1
                    continue
                db.add(
                    WhatsAppEvent(
                        external_id=external_id,
                        event_type=event_type,
                        phone_number_id=phone_number_id,
                        from_number=None,
                        to_number=status.get("recipient_id"),
                        status=status_name,
                        message_type=None,
                        body=None,
                        raw_json=raw,
                    )
                )
                inserted += 1
    if inserted:
        db.commit()
    return inserted, duplicates


@router.get("", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if not settings.whatsapp_verify_token:
        raise HTTPException(status_code=503, detail="WhatsApp verify token is not configured")
    if (
        hub_mode != "subscribe"
        or hub_verify_token != settings.whatsapp_verify_token
        or hub_challenge is None
    ):
        raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification")
    return hub_challenge


@router.post("")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    _verify_signature(raw_body, request.headers.get("x-hub-signature-256"))
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Webhook JSON inválido") from exc
    if payload.get("object") != "whatsapp_business_account":
        raise HTTPException(status_code=400, detail="Unsupported webhook object")
    inserted, duplicates = _store_payload_events(db, payload)
    return {"received": True, "stored": inserted, "duplicates": duplicates}


@ops_router.get("/status")
def whatsapp_status(u: User = Depends(require(Role.ADMIN, Role.SUPERADMIN))):
    return {
        "cloud_api_ready": settings.whatsapp_cloud_ready,
        "verify_token_ready": bool(settings.whatsapp_verify_token),
        "access_token_ready": bool(settings.whatsapp_access_token),
        "phone_number_id_ready": bool(settings.whatsapp_phone_number_id),
        "signature_validation_ready": bool(settings.whatsapp_app_secret),
        "api_version": settings.whatsapp_api_version,
    }


@ops_router.get("/events")
def whatsapp_events(
    limit: int = Query(default=50, ge=1, le=200),
    u: User = Depends(require(Role.ADMIN, Role.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(WhatsAppEvent).order_by(WhatsAppEvent.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "external_id": row.external_id,
            "event_type": row.event_type,
            "from_number": row.from_number,
            "to_number": row.to_number,
            "status": row.status,
            "message_type": row.message_type,
            "body": row.body,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@ops_router.post("/send-test")
async def send_test_message(
    data: WhatsAppSendTestIn,
    u: User = Depends(require(Role.ADMIN, Role.SUPERADMIN)),
):
    if not settings.whatsapp_cloud_ready:
        raise HTTPException(status_code=503, detail="WhatsApp Cloud API no está configurada")
    to = _normalize_phone(data.to)
    if data.mode == "text":
        if not data.text:
            raise HTTPException(status_code=422, detail="El texto es obligatorio en modo text")
        body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": data.text},
        }
    else:
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": data.template_name,
                "language": {"code": data.language_code},
            },
        }

    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo conectar con Meta") from exc

    try:
        result = response.json()
    except ValueError:
        result = {"raw": response.text[:1000]}
    if response.status_code >= 400:
        detail = result.get("error", {}).get("message") if isinstance(result, dict) else None
        raise HTTPException(status_code=502, detail=detail or "Meta rechazó el mensaje")
    return {"sent": True, "meta": result}
