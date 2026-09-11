import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Float, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

def uid(): return str(uuid.uuid4())

class CourierLocation(Base):
    __tablename__='courier_locations'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    courier_id: Mapped[str]=mapped_column(ForeignKey('couriers.id',ondelete='CASCADE'),index=True)
    delivery_id: Mapped[str|None]=mapped_column(ForeignKey('deliveries.id',ondelete='SET NULL'),nullable=True,index=True)
    latitude: Mapped[float]=mapped_column(Float)
    longitude: Mapped[float]=mapped_column(Float)
    accuracy: Mapped[float|None]=mapped_column(Float,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class Notification(Base):
    __tablename__='notifications'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True)
    order_id: Mapped[str|None]=mapped_column(ForeignKey('orders.id',ondelete='CASCADE'),nullable=True,index=True)
    kind: Mapped[str]=mapped_column(String(60),default='ORDER')
    title: Mapped[str]=mapped_column(String(160))
    body: Mapped[str]=mapped_column(Text)
    read: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
