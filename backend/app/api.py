from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import *
from app.schemas import *
from app.security import verify_password, make_token, current_user, require
router=APIRouter(prefix='/api/v1')

def product_dict(p:Product, business=None):
    return {'id':p.id,'business_id':p.business_id,'category_id':p.category_id,'name':p.name,'description':p.description,'image_url':p.image_url,'price':float(p.price),'currency':p.currency,'stock':p.stock,'unit':p.unit,'active':p.active,'business_name': business.name if business else None}
@router.get('/health')
def health(): return {'ok':True,'service':'LAYA Market API'}
@router.post('/auth/login', response_model=TokenOut)
def login(data:LoginIn, db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==data.email.lower()))
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,'Credenciales inválidas')
    return TokenOut(access_token=make_token(u),role=u.role.value,name=u.name)
@router.get('/me')
def me(u:User=Depends(current_user)): return {'id':u.id,'email':u.email,'name':u.name,'role':u.role.value,'country':u.country}
@router.get('/categories')
def categories(db:Session=Depends(get_db)):
    return [{'id':x.id,'name':x.name,'slug':x.slug,'icon':x.icon} for x in db.scalars(select(Category).order_by(Category.name)).all()]
@router.get('/businesses')
def businesses(country:str|None=None, db:Session=Depends(get_db)):
    q=select(Business).where(Business.status==BusinessStatus.APPROVED)
    if country: q=q.where(Business.country==country)
    return [{'id':b.id,'name':b.name,'description':b.description,'logo_url':b.logo_url,'country':b.country,'city':b.city,'own_delivery':b.own_delivery,'courier_enabled':b.courier_enabled} for b in db.scalars(q).all()]
@router.get('/products')
def products(category_id:str|None=None,business_id:str|None=None,currency:str|None=None,db:Session=Depends(get_db)):
    q=select(Product).where(Product.active==True, Product.stock>0)
    if category_id:q=q.where(Product.category_id==category_id)
    if business_id:q=q.where(Product.business_id==business_id)
    if currency:q=q.where(Product.currency==currency)
    items=db.scalars(q.order_by(Product.created_at.desc())).all(); bids={p.business_id for p in items}; bm={b.id:b for b in db.scalars(select(Business).where(Business.id.in_(bids))).all()} if bids else {}
    return [product_dict(p,bm.get(p.business_id)) for p in items]
@router.get('/products/{pid}')
def product(pid:str,db:Session=Depends(get_db)):
    p=db.get(Product,pid)
    if not p: raise HTTPException(404,'Producto no encontrado')
    return product_dict(p,db.get(Business,p.business_id))
@router.post('/orders')
def create_order(data:OrderIn,u:User=Depends(require(Role.CUSTOMER,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.get(Business,data.business_id)
    if not b or b.status!=BusinessStatus.APPROVED: raise HTTPException(400,'Comercio no disponible')
    subtotal=0; resolved=[]
    for i in data.items:
        p=db.get(Product,i.product_id)
        if not p or p.business_id!=b.id or not p.active: raise HTTPException(400,'Producto inválido')
        if p.stock<i.quantity: raise HTTPException(400,f'Stock insuficiente: {p.name}')
        if p.currency!=data.currency: raise HTTPException(400,'Todos los productos deben usar la moneda del pedido')
        subtotal+=float(p.price)*i.quantity; resolved.append((p,i.quantity))
    total=subtotal+data.delivery_fee
    order=Order(customer_id=u.id,business_id=b.id,currency=data.currency,subtotal=subtotal,delivery_fee=data.delivery_fee,total=total,delivery_method=data.delivery_method,delivery_address=data.delivery_address,payment_method=data.payment_method)
    db.add(order); db.flush()
    for p,q in resolved:
        p.stock-=q; db.add(OrderItem(order_id=order.id,product_id=p.id,name=p.name,quantity=q,unit_price=p.price,subtotal=float(p.price)*q))
    db.add(Payment(order_id=order.id,provider='SIMULATED' if data.payment_method=='SIMULATED' else data.payment_method,status=PaymentStatus.PENDING,amount=total,currency=data.currency))
    db.commit(); return {'id':order.id,'status':order.status.value,'total':total,'currency':order.currency}
@router.get('/orders/my')
def my_orders(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Order).where(Order.customer_id==u.id).order_by(Order.created_at.desc())).all()
    return [order_view(o,db) for o in rows]
def order_view(o,db):
    items=db.scalars(select(OrderItem).where(OrderItem.order_id==o.id)).all(); b=db.get(Business,o.business_id)
    return {'id':o.id,'business_id':o.business_id,'business_name':b.name if b else '', 'status':o.status.value,'currency':o.currency,'subtotal':float(o.subtotal),'delivery_fee':float(o.delivery_fee),'total':float(o.total),'delivery_method':o.delivery_method,'delivery_address':o.delivery_address,'payment_method':o.payment_method,'created_at':o.created_at.isoformat(),'items':[{'product_id':i.product_id,'name':i.name,'quantity':i.quantity,'unit_price':float(i.unit_price)} for i in items]}
@router.post('/payments/intent')
def payment_intent(data:PaymentIntentIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,data.order_id)
    if not o: raise HTTPException(404,'Pedido no encontrado')
    return {'provider':data.provider,'order_id':o.id,'amount':float(o.total),'currency':o.currency,'checkout_url':None,'mode':'sandbox','message':'Vista preparada. Conecta credenciales reales del proveedor para checkout externo.'}
@router.post('/payments/{order_id}/simulate-approve')
def approve_payment(order_id:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(Payment).where(Payment.order_id==order_id));
    if not p: raise HTTPException(404,'Pago no encontrado')
    p.status=PaymentStatus.APPROVED; db.commit(); return {'ok':True,'status':p.status.value}
# Merchant
@router.get('/merchant/business')
def merchant_business(u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id));
    if not b: raise HTTPException(404,'Negocio no encontrado')
    return {'id':b.id,'name':b.name,'status':b.status.value,'country':b.country,'city':b.city,'own_delivery':b.own_delivery,'courier_enabled':b.courier_enabled}
@router.get('/merchant/products')
def merchant_products(u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id));
    if not b: return []
    return [product_dict(p,b) for p in db.scalars(select(Product).where(Product.business_id==b.id).order_by(Product.created_at.desc())).all()]
@router.post('/merchant/products')
def merchant_create_product(data:ProductIn,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id));
    if not b: raise HTTPException(404,'Negocio no encontrado')
    p=Product(business_id=b.id,**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return product_dict(p,b)
@router.put('/merchant/products/{pid}')
def merchant_update_product(pid:str,data:ProductIn,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id)); p=db.get(Product,pid)
    if not p or not b or p.business_id!=b.id: raise HTTPException(404,'Producto no encontrado')
    for k,v in data.model_dump().items(): setattr(p,k,v)
    db.commit(); return product_dict(p,b)
@router.delete('/merchant/products/{pid}')
def merchant_delete_product(pid:str,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id)); p=db.get(Product,pid)
    if not p or not b or p.business_id!=b.id: raise HTTPException(404,'Producto no encontrado')
    p.active=False; db.commit(); return {'ok':True}
@router.get('/merchant/orders')
def merchant_orders(u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id));
    if not b:return []
    return [order_view(o,db) for o in db.scalars(select(Order).where(Order.business_id==b.id).order_by(Order.created_at.desc())).all()]
@router.patch('/merchant/orders/{oid}/status')
def merchant_order_status(oid:str,status:OrderStatus,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id)); o=db.get(Order,oid)
    if not o or not b or o.business_id!=b.id: raise HTTPException(404,'Pedido no encontrado')
    o.status=status; db.commit(); return {'ok':True,'status':o.status.value}
@router.post('/merchant/orders/{oid}/request-courier')
def request_courier(oid:str,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id)); o=db.get(Order,oid)
    if not o or not b or o.business_id!=b.id: raise HTTPException(404,'Pedido no encontrado')
    d=db.scalar(select(Delivery).where(Delivery.order_id==oid)) or Delivery(order_id=oid,fee=o.delivery_fee); db.add(d); o.status=OrderStatus.COURIER_REQUESTED; db.commit(); return {'ok':True,'delivery_id':d.id}
# Admin
@router.get('/admin/summary')
def admin_summary(u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    return {'businesses':len(db.scalars(select(Business)).all()),'pending_businesses':len(db.scalars(select(Business).where(Business.status==BusinessStatus.PENDING)).all()),'orders':len(db.scalars(select(Order)).all()),'couriers_available':len(db.scalars(select(Courier).where(Courier.available==True)).all())}
@router.get('/admin/businesses')
def admin_businesses(u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    return [{'id':b.id,'name':b.name,'country':b.country,'city':b.city,'status':b.status.value,'created_at':b.created_at.isoformat()} for b in db.scalars(select(Business).order_by(Business.created_at.desc())).all()]
@router.patch('/admin/businesses/{bid}/status')
def admin_business_status(bid:str,status:BusinessStatus,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.get(Business,bid)
    if not b: raise HTTPException(404,'Negocio no encontrado')
    b.status=status;db.commit();return {'ok':True,'status':b.status.value}
@router.get('/admin/deliveries')
def admin_deliveries(u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    rows=db.scalars(select(Delivery).order_by(Delivery.created_at.desc())).all(); return [{'id':d.id,'order_id':d.order_id,'courier_id':d.courier_id,'status':d.status,'fee':float(d.fee)} for d in rows]
@router.get('/admin/couriers')
def admin_couriers(u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    return [{'id':c.id,'name':c.name,'phone':c.phone,'country':c.country,'city':c.city,'available':c.available} for c in db.scalars(select(Courier)).all()]
@router.patch('/admin/deliveries/{did}/assign/{cid}')
def assign_courier(did:str,cid:str,u:User=Depends(require(Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    d=db.get(Delivery,did); c=db.get(Courier,cid)
    if not d or not c: raise HTTPException(404,'Entrega o cadete no encontrado')
    d.courier_id=c.id; d.status='ASSIGNED'; c.available=False; o=db.get(Order,d.order_id); o.status=OrderStatus.ON_THE_WAY; db.commit(); return {'ok':True}
