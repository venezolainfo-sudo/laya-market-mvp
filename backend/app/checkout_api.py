from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Address, Business, Delivery, Order, OrderItem, Payment, PaymentStatus, Role, User
from app.schemas import BusinessDeliveryIn, CheckoutQuoteIn, OrderIn
from app.security import current_user, require
from app.checkout_service import quote_checkout

router=APIRouter(prefix='/api/v1')

def quote_view(q):
    b=q['business']; a=q['address']
    return {'business_id':b.id,'business_name':b.name,'currency':q['resolved'][0]['product'].currency if q['resolved'] else None,'coverage':q['coverage'],'delivery_method':q['delivery_method'],'distance_km':q['distance_km'],'delivery_radius_km':b.delivery_radius_km,'subtotal':q['subtotal'],'delivery_fee':q['delivery_fee'],'total':q['total'],'address':None if not a else {'id':a.id,'label':a.label,'line1':a.line1,'city':a.city,'province':a.province,'country':a.country,'latitude':a.latitude,'longitude':a.longitude},'items':[{'product_id':x['product'].id,'name':x['product'].name,'presentation_id':x['presentation'].id if x['presentation'] else None,'presentation_label':x['presentation'].label if x['presentation'] else None,'quantity':x['quantity'],'unit_price':x['unit_price'],'subtotal':x['subtotal']} for x in q['resolved']]}

def delivery_view(b:Business):
    return {'business_id':b.id,'latitude':b.latitude,'longitude':b.longitude,'delivery_radius_km':b.delivery_radius_km,'delivery_base_fee':float(b.delivery_base_fee),'delivery_per_km':float(b.delivery_per_km),'delivery_min_fee':float(b.delivery_min_fee),'own_delivery':b.own_delivery,'courier_enabled':b.courier_enabled,'pickup_enabled':b.pickup_enabled}

@router.post('/checkout/quote')
def checkout_quote(data:CheckoutQuoteIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    return quote_view(quote_checkout(db,u,data.business_id,data.items,data.currency,data.delivery_method,data.address_id))

@router.post('/checkout/order')
def checkout_order(data:OrderIn,u:User=Depends(require(Role.CUSTOMER,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    q=quote_checkout(db,u,data.business_id,data.items,data.currency,data.delivery_method,data.address_id,lock=True); b=q['business']; a=q['address']; delivery_address='' if not a else f'{a.line1}, {a.city}, {a.province}'
    o=Order(customer_id=u.id,business_id=b.id,address_id=a.id if a else None,currency=data.currency,subtotal=q['subtotal'],delivery_fee=q['delivery_fee'],total=q['total'],delivery_method=data.delivery_method,delivery_address=delivery_address,delivery_latitude=a.latitude if a else None,delivery_longitude=a.longitude if a else None,distance_km=q['distance_km'],customer_name=u.name,customer_phone=u.phone,notes=data.notes,payment_method=data.payment_method);db.add(o);db.flush()
    for x in q['resolved']:
        p=x['product'];pr=x['presentation'];qty=x['quantity'];
        if pr: pr.stock-=qty
        else: p.stock-=qty
        db.add(OrderItem(order_id=o.id,product_id=p.id,presentation_id=pr.id if pr else None,name=p.name,presentation_label=pr.label if pr else None,quantity=qty,unit_price=x['unit_price'],subtotal=x['subtotal']))
    db.add(Payment(order_id=o.id,provider=data.payment_method,status=PaymentStatus.PENDING,amount=q['total'],currency=data.currency))
    if data.delivery_method=='COURIER':db.add(Delivery(order_id=o.id,fee=q['delivery_fee']))
    db.commit();db.refresh(o);return {'id':o.id,'status':o.status.value,'payment_status':PaymentStatus.PENDING.value,'currency':o.currency,'subtotal':float(o.subtotal),'delivery_fee':float(o.delivery_fee),'total':float(o.total),'distance_km':o.distance_km,'delivery_method':o.delivery_method,'delivery_address':o.delivery_address}

@router.get('/checkout/orders/my')
def checkout_orders(u:User=Depends(current_user),db:Session=Depends(get_db)):
    orders=db.scalars(select(Order).where(Order.customer_id==u.id).order_by(Order.created_at.desc())).all();out=[]
    for o in orders:
        items=db.scalars(select(OrderItem).where(OrderItem.order_id==o.id)).all();pay=db.scalar(select(Payment).where(Payment.order_id==o.id));out.append({'id':o.id,'business_id':o.business_id,'status':o.status.value,'payment_status':pay.status.value if pay else 'PENDING','currency':o.currency,'subtotal':float(o.subtotal),'delivery_fee':float(o.delivery_fee),'total':float(o.total),'delivery_method':o.delivery_method,'delivery_address':o.delivery_address,'delivery_latitude':o.delivery_latitude,'delivery_longitude':o.delivery_longitude,'distance_km':o.distance_km,'customer_name':o.customer_name,'customer_phone':o.customer_phone,'notes':o.notes,'created_at':o.created_at.isoformat(),'items':[{'product_id':i.product_id,'presentation_id':i.presentation_id,'name':i.name,'presentation_label':i.presentation_label,'quantity':i.quantity,'unit_price':float(i.unit_price),'subtotal':float(i.subtotal)} for i in items]})
    return out

@router.get('/merchant/business/delivery')
def get_merchant_delivery(u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id))
    if not b:raise HTTPException(404,'Negocio no encontrado')
    return delivery_view(b)

@router.put('/merchant/business/delivery')
def merchant_delivery_settings(data:BusinessDeliveryIn,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id))
    if not b:raise HTTPException(404,'Negocio no encontrado')
    for k,v in data.model_dump().items():setattr(b,k,v)
    db.commit();return {'ok':True,**delivery_view(b)}
