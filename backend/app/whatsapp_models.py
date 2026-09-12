import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def uid():
    return str(uuid.uuid4())


class WhatsAppEvent(Base):
    __tablename__ = "whatsapp_events"
    __table_args__ = (UniqueConstraint("external_id", "event_type", name="uq_whatsapp_event_external_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    external_id: Mapped[str] = mapped_column(String(160), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    from_number: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    to_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    message_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
