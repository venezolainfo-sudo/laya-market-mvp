import enum, uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

def uid(): return str(uuid.uuid4())
class Role(str, enum.Enum):
    CUSTOMER='CUSTOMER'; MERCHANT='MERCHANT'; MERCHANT_STAFF='MERCHANT_STAFF'; COURIER='COURIER'; ADMIN='ADMIN'; SUPERADMIN='SUPERADMIN'
class BusinessStatus(str, enum.Enum): PENDING='PENDING'; APPROVED='APPROVED'; SUSPENDED='SUSPENDED'; REJECTED='REJECTED'
class OrderStatus(str, enum.Enum): NEW='NEW'; ACCEPTED='ACCEPTED'; PREPARING='PREPARING'; READY='READY'; COURIER_REQUESTED='COURIER_REQUESTED'; ON_THE_WAY='ON_THE_WAY'; DELIVERED='DELIVERED'; CANCELLED='CANCELLED'
class PaymentStatus(str, enum.Enum): PENDING='PENDING'; APPROVED='APPROVED'; REJECTED='REJECTED'; REFUNDED='REFUNDED'
class User(Base):
    __tablename__='users'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str]=mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    name: Mapped[str]=mapped_column(String(120))
    phone: Mapped[str|None]=mapped_column(String(40), nullable=True)
    role: Mapped[Role]=mapped_column(Enum(Role), default=Role.CUSTOMER)
    country: Mapped[str]=mapped_column(String(2), default='AR')
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Address(Base):
    __tablename__='addresses'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    label: Mapped[str]=mapped_column(String(50), default='Casa')
    line1: Mapped[str]=mapped_column(String(220)); city: Mapped[str]=mapped_column(String(120)); province: Mapped[str]=mapped_column(String(120)); country: Mapped[str]=mapped_column(String(2)); postal_code: Mapped[str|None]=mapped_column(String(20), nullable=True)
class Business(Base):
    __tablename__='businesses'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str]=mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str]=mapped_column(String(140)); description: Mapped[str|None]=mapped_column(Text, nullable=True)
    logo_url: Mapped[str|None]=mapped_column(String(500), nullable=True)
    country: Mapped[str]=mapped_column(String(2), default='AR'); city: Mapped[str]=mapped_column(String(120), default='Mendoza')
    address: Mapped[str]=mapped_column(String(220), default=''); status: Mapped[BusinessStatus]=mapped_column(Enum(BusinessStatus), default=BusinessStatus.PENDING)
    own_delivery: Mapped[bool]=mapped_column(Boolean, default=True); courier_enabled: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Category(Base):
    __tablename__='categories'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); name: Mapped[str]=mapped_column(String(100), unique=True); slug: Mapped[str]=mapped_column(String(100), unique=True); icon: Mapped[str]=mapped_column(String(20), default='🛒')
class Product(Base):
    __tablename__='products'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    business_id: Mapped[str]=mapped_column(ForeignKey('businesses.id'), index=True); category_id: Mapped[str]=mapped_column(ForeignKey('categories.id'), index=True)
    name: Mapped[str]=mapped_column(String(160)); description: Mapped[str|None]=mapped_column(Text, nullable=True); image_url: Mapped[str|None]=mapped_column(String(500), nullable=True)
    price: Mapped[float]=mapped_column(Numeric(12,2)); currency: Mapped[str]=mapped_column(String(3), default='ARS'); stock: Mapped[int]=mapped_column(Integer, default=0); unit: Mapped[str]=mapped_column(String(40), default='unidad'); active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Order(Base):
    __tablename__='orders'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); customer_id: Mapped[str]=mapped_column(ForeignKey('users.id')); business_id: Mapped[str]=mapped_column(ForeignKey('businesses.id'), index=True)
    status: Mapped[OrderStatus]=mapped_column(Enum(OrderStatus), default=OrderStatus.NEW); currency: Mapped[str]=mapped_column(String(3), default='ARS'); subtotal: Mapped[float]=mapped_column(Numeric(12,2)); delivery_fee: Mapped[float]=mapped_column(Numeric(12,2), default=0); total: Mapped[float]=mapped_column(Numeric(12,2)); delivery_method: Mapped[str]=mapped_column(String(30), default='OWN_DELIVERY'); delivery_address: Mapped[str]=mapped_column(String(350)); payment_method: Mapped[str]=mapped_column(String(40), default='CASH'); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class OrderItem(Base):
    __tablename__='order_items'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); order_id: Mapped[str]=mapped_column(ForeignKey('orders.id', ondelete='CASCADE')); product_id: Mapped[str]=mapped_column(ForeignKey('products.id')); name: Mapped[str]=mapped_column(String(160)); quantity: Mapped[int]=mapped_column(Integer); unit_price: Mapped[float]=mapped_column(Numeric(12,2)); subtotal: Mapped[float]=mapped_column(Numeric(12,2))
class Payment(Base):
    __tablename__='payments'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); order_id: Mapped[str]=mapped_column(ForeignKey('orders.id')); provider: Mapped[str]=mapped_column(String(40), default='SIMULATED'); status: Mapped[PaymentStatus]=mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING); amount: Mapped[float]=mapped_column(Numeric(12,2)); currency: Mapped[str]=mapped_column(String(3)); external_reference: Mapped[str|None]=mapped_column(String(160), nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Courier(Base):
    __tablename__='couriers'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); user_id: Mapped[str|None]=mapped_column(ForeignKey('users.id'), nullable=True); name: Mapped[str]=mapped_column(String(120)); phone: Mapped[str]=mapped_column(String(40)); country: Mapped[str]=mapped_column(String(2), default='AR'); city: Mapped[str]=mapped_column(String(120), default='Mendoza'); available: Mapped[bool]=mapped_column(Boolean, default=True)
class Delivery(Base):
    __tablename__='deliveries'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); order_id: Mapped[str]=mapped_column(ForeignKey('orders.id'), unique=True); courier_id: Mapped[str|None]=mapped_column(ForeignKey('couriers.id'), nullable=True); status: Mapped[str]=mapped_column(String(30), default='REQUESTED'); fee: Mapped[float]=mapped_column(Numeric(12,2), default=0); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
