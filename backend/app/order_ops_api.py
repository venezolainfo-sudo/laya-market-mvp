from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Business, Delivery, Order, OrderItem, OrderStatus, Payment, PaymentStatus, Product, ProductPresentation, Role, User
from app.security import require

router = APIRouter(prefix='/api/v1')

STATUS_LABELS = {
    'NEW':'RECIBIDO','ACCEPTED':'ACEPTADO','PREPARING':'PREPARANDO','READY':'LISTO',
    'COURIER_REQUESTED':'CADETE_SOLICITADO','ASSIGNED':'ASIGNADO','PICKED_UP':'RETIRADO',
    'ON_THE_WAY':'EN_CAMINO','DELIVERED':'ENTREGADO','CANCELLED':'CANCELADO'
}
ALLOWED = {
    OrderStatus.NEW:{OrderStatus.ACCEPTED,OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED:{OrderStatus.PREPARING,OrderStatus.CANCELLED},
    OrderStatus.PREPARING:{OrderStatus.READY,OrderStatus.CANCELLED},
    OrderStatus.READY:{OrderStatus.COURIER_REQUESTED,OrderStatus.ASSIGNED,OrderStatus.PICKED_UP,OrderStatus.DELIVERED,OrderStatus.CANCELLED},
    OrderStatus.COURIER_REQUESTED:{OrderStatus.ASSIGNED,OrderStatus.CANCELLED},
    OrderStatus.ASSIGNED:{OrderStatus.PICKED_UP,OrderStatus.CANCELLED},
    OrderStatus.PICKED_UP:{OrderStatus.ON_THE_WAY,OrderStatus.CANCELLED},
    OrderStatus.ON_THE_WAY:{OrderStatus.DELIVERED},
    OrderStatus.DELIVERED:set(), OrderStatus.CANCELLED:set()
}

class StatusIn(BaseModel):
    status: OrderStatus
class CancelIn(BaseModel):
    reason: str = Field(min_length=3,max_length=500)

def get_business_for_user(db:Session,u:User):
    b=db.scalar(select(Business).where(Business.owner_id==u.id))
    if not b: raise HTTPException(404,'Negocio no encontrado')
    return b

def order_detail(db:Session,o:Order):
    b=db.get(Business,o.business_id); pay=db.scalar(select(Payment).where(Payment.order_id==o.id)); delivery=db.scalar(select(Delivery).where(Delivery.order_id==o.id)); items=db.scalars(select(OrderItem).where(OrderItem.order_id==o.id)).all()
    return {
        'id':o.id,'business_id':o.business_id,'business_name':b.name if b else '',
        'customer_id':o.customer_id,'customer_name':o.customer_name,'customer_phone':o.customer_phone,
        'status':o.status.value,'status_label':STATUS_LABELS[o.status.value],
        'currency':o.currency,'subtotal':float(o.subtotal),'delivery_fee':float(o.delivery_fee),'total':float(o.total),
        'delivery_method':o.delivery_method,'delivery_address':o.delivery_address,'delivery_latitude':o.delivery_latitude,'delivery_longitude':o.delivery_longitude,'distance_km':o.distance_km,
        'payment_method':o.payment_method,'payment_status':pay.status.value if pay else 'PENDING','notes':o.notes,
        'cancellation_reason':o.cancellation_reason,'cancelled_by':o.cancelled_by,
        'created_at':o.created_at.isoformat(),'updated_at':(o.updated_at or o.created_at).isoformat(),
        'delivery':None if not delivery else {'id':delivery.id,'courier_id':delivery.courier_id,'status':delivery.status,'fee':float(delivery.fee)},
        'items':[{'id':i.id,'product_id':i.product_id,'presentation_id':i.presentation_id,'name':i.name,'presentation_label':i.presentation_label,'quantity':i.quantity,'unit_price':float(i.unit_price),'subtotal':float(i.subtotal)} for i in items]
    }

def apply_status(db:Session,o:Order,new:OrderStatus):
    if new==o.status:return
    if new not in ALLOWED.get(o.status,set()):raise HTTPException(409,f'Transición no permitida: {o.status.value} → {new.value}')
    o.status=new;o.updated_at=datetime.utcnow()
    d=db.scalar(select(Delivery).where(Delivery.order_id==o.id))
    if d:
        mapping={OrderStatus.COURIER_REQUESTED:'REQUESTED',OrderStatus.ASSIGNED:'ASSIGNED',OrderStatus.PICKED_UP:'PICKED_UP',OrderStatus.ON_THE_WAY:'ON_THE_WAY',OrderStatus.DELIVERED:'DELIVERED',OrderStatus.CANCELLED:'CANCELLED'}
        if new in mapping:d.status=mapping[new]

def cancel_order(db:Session,o:Order,reason:str,actor:str):
    if o.status in {OrderStatus.DELIVERED,OrderStatus.CANCELLED}:raise HTTPException(409,'Este pedido ya no puede cancelarse')
    items=db.scalars(select(OrderItem).where(OrderItem.order_id==o.id)).all()
    for i in items:
        if i.presentation_id:
            pr=db.get(ProductPresentation,i.presentation_id)
            if pr:pr.stock+=i.quantity
        else:
            p=db.get(Product,i.product_id)
            if p:p.stock+=i.quantity
    o.status=OrderStatus.CANCELLED;o.cancellation_reason=reason;o.cancelled_by=actor;o.updated_at=datetime.utcnow()
    p=db.scalar(select(Payment).where(Payment.order_id==o.id))
    if p and p.status==PaymentStatus.APPROVED:p.status=PaymentStatus.REFUNDED
    d=db.scalar(select(Delivery).where(Delivery.order_id==o.id))
    if d:d.status='CANCELLED'

@router.get('/merchant/order-management')
def merchant_orders(u:User=Depends(require(Role.MERCHANT,Role.MERCHANT_STAFF,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=get_business_for_user(db,u)
    return [order_detail(db,o) for o in db.scalars(select(Order).where(Order.business_id==b.id).order_by(Order.created_at.desc())).all()]

@router.get('/merchant/order-management/{oid}')
def merchant_order(oid:str,u:User=Depends(require(Role.MERCHANT,Role.MERCHANT_STAFF,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=get_business_for_user(db,u);o=db.get(Order,oid)
    if not o or o.business_id!=b.id:raise HTTPException(404,'Pedido no encontrado')
    return order_detail(db,o)

@router.patch('/merchant/order-management/{oid}/status')
def merchant_status(oid:str,data:StatusIn,u:User=Depends(require(Role.MERCHANT,Role.MERCHANT_STAFF,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=get_business_for_user(db,u);o=db.get(Order,oid)
    if not o or o.business_id!=b.id:raise HTTPException(404,'Pedido no encontrado')
    apply_status(db,o,data.status);db.commit();db.refresh(o);return order_detail(db,o)

@router.post('/merchant/order-management/{oid}/cancel')
def merchant_cancel(oid:str,data:CancelIn,u:User=Depends(require(Role.MERCHANT,Role.MERCHANT_STAFF,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=get_business_for_user(db,u);o=db.get(Order,oid)
    if not o or o.business_id!=b.id:raise HTTPException(404,'Pedido no encontrado')
    cancel_order(db,o,data.reason,'MERCHANT');db.commit();db.refresh(o);return order_detail(db,o)

@router.get('/merchant/order-notifications')
def merchant_notifications(u:User=Depends(require(Role.MERCHANT,Role.MERCHANT_STAFF,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=get_business_for_user(db,u);rows=db.scalars(select(Order).where(Order.business_id==b.id,Order.status==OrderStatus.NEW).order_by(Order.created_at.desc()).limit(10)).all()
    return {'new_order_count':len(rows),'orders':[{'id':o.id,'customer_name':o.customer_name,'total':float(o.total),'currency':o.currency,'created_at':o.created_at.isoformat()} for o in rows]}

@router.get('/admin/order-management')
def admin_orders(business_id:str|None=None,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    q=select(Order)
    if business_id:q=q.where(Order.business_id==business_id)
    return [order_detail(db,o) for o in db.scalars(q.order_by(Order.created_at.desc())).all()]

@router.get('/admin/order-management/{oid}')
def admin_order(oid:str,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    o=db.get(Order,oid)
    if not o:raise HTTPException(404,'Pedido no encontrado')
    return order_detail(db,o)

@router.patch('/admin/order-management/{oid}/status')
def admin_status(oid:str,data:StatusIn,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    o=db.get(Order,oid)
    if not o:raise HTTPException(404,'Pedido no encontrado')
    apply_status(db,o,data.status);db.commit();db.refresh(o);return order_detail(db,o)

@router.post('/admin/order-management/{oid}/cancel')
def admin_cancel(oid:str,data:CancelIn,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    o=db.get(Order,oid)
    if not o:raise HTTPException(404,'Pedido no encontrado')
    cancel_order(db,o,data.reason,'ADMIN');db.commit();db.refresh(o);return order_detail(db,o)
