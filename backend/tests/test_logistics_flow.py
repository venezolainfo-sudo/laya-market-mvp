from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import SessionLocal
from app.models import Address,Business,Courier,Delivery,Product,User,Role

client=TestClient(app)

def data():
    db=SessionLocal()
    try:
        customer=db.scalar(select(User).where(User.role==Role.CUSTOMER));business=db.scalar(select(Business).where(Business.name=='Mercado Demo LAYA'));product=db.scalar(select(Product).where(Product.business_id==business.id));address=db.scalar(select(Address).where(Address.user_id==customer.id));courier=db.scalar(select(Courier).where(Courier.user_id.is_not(None)))
        return business.id,product.id,address.id,product.currency,courier.id
    finally:db.close()

def create_courier_order():
    bid,pid,aid,currency,_=data();r=client.post('/api/v1/checkout/order',json={'business_id':bid,'items':[{'product_id':pid,'quantity':1}],'currency':currency,'delivery_method':'COURIER','address_id':aid,'payment_method':'SIMULATED','notes':'logistics-ci'});assert r.status_code==200,r.text;return r.json()['id']

def test_whatsapp_business_contact_is_wired():
    r=client.get('/api/v1/whatsapp/contact');assert r.status_code==200;assert r.json()['phone']=='+5492612779620';assert 'wa.me/5492612779620' in r.json()['url']

def test_full_courier_tracking_and_customer_notifications():
    oid=create_courier_order()
    for status in ['ACCEPTED','PREPARING','READY','COURIER_REQUESTED']:
        r=client.patch(f'/api/v1/merchant/order-management/{oid}/status',json={'status':status});assert r.status_code==200,r.text
    db=SessionLocal()
    try:
        d=db.scalar(select(Delivery).where(Delivery.order_id==oid));cid=db.scalar(select(Courier).where(Courier.user_id.is_not(None))).id;did=d.id
    finally:db.close()
    r=client.patch(f'/api/v1/admin/logistics/deliveries/{did}/assign/{cid}');assert r.status_code==200,r.text;assert r.json()['status']=='ASSIGNED'
    r=client.post('/api/v1/courier/location',json={'latitude':-32.89,'longitude':-68.84,'accuracy':5,'delivery_id':did});assert r.status_code==200,r.text
    r=client.get(f'/api/v1/tracking/orders/{oid}');assert r.status_code==200,r.text;assert r.json()['location'] is not None;assert r.json()['courier'] is not None
    for status in ['PICKED_UP','ON_THE_WAY','DELIVERED']:
        r=client.patch(f'/api/v1/courier/deliveries/{did}/status',json={'status':status});assert r.status_code==200,r.text;assert r.json()['status']==status
    notes=client.get('/api/v1/notifications/my');assert notes.status_code==200;assert any(n['order_id']==oid and n['title']=='Pedido entregado' for n in notes.json())
