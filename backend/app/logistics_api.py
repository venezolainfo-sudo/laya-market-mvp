from datetime import datetime, timezone
from urllib.parse import quote
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models import Business,Courier,Delivery,Order,OrderStatus,Role,User
from app.logistics_models import CourierLocation,Notification
from app.security import current_user,require

router=APIRouter(prefix='/api/v1')

class LocationIn(BaseModel):
    latitude: float=Field(ge=-90,le=90)
    longitude: float=Field(ge=-180,le=180)
    accuracy: float|None=None
    delivery_id: str|None=None
class AvailabilityIn(BaseModel): available: bool
class DeliveryStatusIn(BaseModel): status: str

STATUS_TEXT={'NEW':('Pedido recibido','Tu pedido fue recibido por el comercio.'),'ACCEPTED':('Pedido aceptado','El comercio aceptó tu pedido.'),'PREPARING':('Preparando pedido','Tu pedido está siendo preparado.'),'READY':('Pedido listo','Tu pedido ya está listo para salir.'),'COURIER_REQUESTED':('Buscando cadete','Estamos asignando un cadete a tu pedido.'),'ASSIGNED':('Cadete asignado','Ya hay un cadete asignado a tu pedido.'),'PICKED_UP':('Pedido retirado','El cadete retiró tu pedido del comercio.'),'ON_THE_WAY':('Pedido en camino','Tu pedido va en camino.'),'DELIVERED':('Pedido entregado','Tu pedido fue marcado como entregado.'),'CANCELLED':('Pedido cancelado','El pedido fue cancelado.')}

def add_notification(db:Session,o:Order,status:str|None=None):
    st=status or o.status.value;title,body=STATUS_TEXT.get(st,('Actualización de pedido',f'El pedido cambió a {st}.'));db.add(Notification(user_id=o.customer_id,order_id=o.id,kind='ORDER_STATUS',title=title,body=body))
def courier_for_user(db:Session,u:User):
    c=db.scalar(select(Courier).where(Courier.user_id==u.id))
    if not c:raise HTTPException(404,'Perfil de cadete no encontrado')
    return c
def order_payload(db:Session,o:Order):
    d=db.scalar(select(Delivery).where(Delivery.order_id==o.id));b=db.get(Business,o.business_id);return {'id':o.id,'business_name':b.name if b else '', 'status':o.status.value,'delivery_method':o.delivery_method,'delivery_address':o.delivery_address,'delivery_latitude':o.delivery_latitude,'delivery_longitude':o.delivery_longitude,'customer_name':o.customer_name,'customer_phone':o.customer_phone,'total':float(o.total),'currency':o.currency,'delivery':None if not d else {'id':d.id,'courier_id':d.courier_id,'status':d.status}}

def _can_view_order(db:Session,u:User,o:Order):
    if u.role in {Role.ADMIN,Role.SUPERADMIN} or o.customer_id==u.id:return True
    if u.role in {Role.MERCHANT,Role.MERCHANT_STAFF}:
        b=db.get(Business,o.business_id)
        return bool(b and b.owner_id==u.id)
    return False

@router.get('/whatsapp/contact')
def whatsapp_contact(order_id:str|None=None,u:User=Depends(current_user),db:Session=Depends(get_db)):
    text='Hola LAYA Market'
    if order_id:
        o=db.get(Order,order_id)
        if not o or not _can_view_order(db,u,o):raise HTTPException(404,'Pedido no encontrado')
        text=f'Hola LAYA Market, consulto por el pedido #{o.id[:8]}.'
    phone=settings.whatsapp_business_number.replace('+','').replace(' ','');return {'phone':settings.whatsapp_business_number,'url':f'https://wa.me/{phone}?text={quote(text)}','automatic_cloud_api_ready':settings.whatsapp_cloud_ready}

@router.get('/notifications/my')
def my_notifications(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Notification).where(Notification.user_id==u.id).order_by(Notification.created_at.desc()).limit(100)).all();return [{'id':n.id,'order_id':n.order_id,'kind':n.kind,'title':n.title,'body':n.body,'read':n.read,'created_at':n.created_at.isoformat()} for n in rows]
@router.get('/notifications/my/summary')
def my_notifications_summary(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Notification).where(Notification.user_id==u.id).order_by(Notification.created_at.desc()).limit(100)).all();return {'unread':sum(1 for n in rows if not n.read),'latest':None if not rows else {'id':rows[0].id,'title':rows[0].title,'body':rows[0].body,'created_at':rows[0].created_at.isoformat()}}
@router.patch('/notifications/{nid}/read')
def read_notification(nid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    n=db.get(Notification,nid)
    if not n or n.user_id!=u.id:raise HTTPException(404,'Notificación no encontrada')
    n.read=True;db.commit();return {'ok':True}

@router.get('/courier/me')
def courier_me(u:User=Depends(require(Role.COURIER)),db:Session=Depends(get_db)):
    c=courier_for_user(db,u);return {'id':c.id,'name':c.name,'phone':c.phone,'city':c.city,'country':c.country,'available':c.available}
@router.patch('/courier/availability')
def courier_availability(data:AvailabilityIn,u:User=Depends(require(Role.COURIER)),db:Session=Depends(get_db)):
    c=courier_for_user(db,u);c.available=data.available;db.commit();return {'ok':True,'available':c.available}
@router.get('/courier/deliveries')
def courier_deliveries(u:User=Depends(require(Role.COURIER)),db:Session=Depends(get_db)):
    c=courier_for_user(db,u);ds=db.scalars(select(Delivery).where(Delivery.courier_id==c.id).order_by(Delivery.created_at.desc())).all();return [order_payload(db,db.get(Order,d.order_id)) for d in ds]
@router.post('/courier/location')
def courier_location(data:LocationIn,u:User=Depends(require(Role.COURIER)),db:Session=Depends(get_db)):
    c=courier_for_user(db,u)
    if data.delivery_id:
        d=db.get(Delivery,data.delivery_id)
        if not d or d.courier_id!=c.id:raise HTTPException(403,'Entrega no asignada a este cadete')
        o=db.get(Order,d.order_id)
        if o.status not in {OrderStatus.ASSIGNED,OrderStatus.PICKED_UP,OrderStatus.ON_THE_WAY}:raise HTTPException(409,'Esta entrega no admite tracking activo')
    db.add(CourierLocation(courier_id=c.id,delivery_id=data.delivery_id,latitude=data.latitude,longitude=data.longitude,accuracy=data.accuracy,created_at=datetime.utcnow()));db.commit();return {'ok':True}
@router.patch('/courier/deliveries/{did}/status')
def courier_delivery_status(did:str,data:DeliveryStatusIn,u:User=Depends(require(Role.COURIER)),db:Session=Depends(get_db)):
    c=courier_for_user(db,u);d=db.get(Delivery,did)
    if not d or d.courier_id!=c.id:raise HTTPException(404,'Entrega no encontrada')
    o=db.get(Order,d.order_id);target=data.status.upper();allowed={'ASSIGNED':'PICKED_UP','PICKED_UP':'ON_THE_WAY','ON_THE_WAY':'DELIVERED'}
    if allowed.get(o.status.value)!=target:raise HTTPException(409,f'Transición no permitida: {o.status.value} → {target}')
    o.status=OrderStatus(target);o.updated_at=datetime.utcnow();d.status=target
    if target=='DELIVERED':c.available=True
    add_notification(db,o,target);db.commit();return order_payload(db,o)

def _assign(db:Session,did:str,cid:str):
    d=db.get(Delivery,did);c=db.get(Courier,cid)
    if not d or not c:raise HTTPException(404,'Entrega o cadete no encontrado')
    if not c.available:raise HTTPException(409,'Cadete no disponible')
    o=db.get(Order,d.order_id)
    if o.status not in {OrderStatus.COURIER_REQUESTED,OrderStatus.READY}:raise HTTPException(409,'El pedido no está listo para asignación')
    d.courier_id=c.id;d.status='ASSIGNED';c.available=False;o.status=OrderStatus.ASSIGNED;o.updated_at=datetime.utcnow();add_notification(db,o,'ASSIGNED');db.commit();return order_payload(db,o)
@router.patch('/admin/logistics/deliveries/{did}/assign/{cid}')
def admin_assign(did:str,cid:str,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):return _assign(db,did,cid)
@router.patch('/admin/deliveries/{did}/assign/{cid}')
def admin_assign_legacy_path(did:str,cid:str,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):return _assign(db,did,cid)

@router.get('/tracking/orders/{oid}')
def tracking(oid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,oid)
    if not o or not _can_view_order(db,u,o):raise HTTPException(404,'Pedido no encontrado')
    d=db.scalar(select(Delivery).where(Delivery.order_id==oid))
    base={'order_id':oid,'status':o.status.value,'destination':{'latitude':o.delivery_latitude,'longitude':o.delivery_longitude,'address':o.delivery_address}}
    if not d or not d.courier_id:return {**base,'courier':None,'location':None,'tracking_active':False,'stale':False}
    c=db.get(Courier,d.courier_id)
    loc=db.scalar(select(CourierLocation).where(CourierLocation.delivery_id==d.id).order_by(CourierLocation.created_at.desc()))
    if not loc:return {**base,'courier':{'id':c.id,'name':c.name,'phone':c.phone},'location':None,'tracking_active':o.status in {OrderStatus.ASSIGNED,OrderStatus.PICKED_UP,OrderStatus.ON_THE_WAY},'stale':False}
    now=datetime.now(timezone.utc);created=loc.created_at.replace(tzinfo=timezone.utc) if loc.created_at.tzinfo is None else loc.created_at;age=max(0,int((now-created).total_seconds()))
    return {**base,'courier':{'id':c.id,'name':c.name,'phone':c.phone},'location':{'latitude':loc.latitude,'longitude':loc.longitude,'accuracy':loc.accuracy,'updated_at':loc.created_at.isoformat(),'age_seconds':age},'tracking_active':o.status in {OrderStatus.ASSIGNED,OrderStatus.PICKED_UP,OrderStatus.ON_THE_WAY},'stale':age>90}
