from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings

router = APIRouter(prefix="/api/v1/webhooks/whatsapp", tags=["whatsapp"])


@router.get("", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if not settings.whatsapp_verify_token:
        raise HTTPException(status_code=503, detail="WhatsApp verify token is not configured")
    if hub_mode != "subscribe" or hub_verify_token != settings.whatsapp_verify_token or hub_challenge is None:
        raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification")
    return hub_challenge


@router.post("")
async def receive_webhook(request: Request):
    payload = await request.json()
    if payload.get("object") != "whatsapp_business_account":
        raise HTTPException(status_code=400, detail="Unsupported webhook object")
    return {"received": True}
