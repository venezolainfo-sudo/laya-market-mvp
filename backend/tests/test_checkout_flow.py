from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import SessionLocal
from app.models import Address, Business, Order, Product, User, Role

client=TestClient(app)

def seeded():
    db=SessionLocal()
    try:
        customer=db.scalar(select(User).where(User.role==Role.CUSTOMER))
        business=db.scalar(select(Business).where(Business.name=='Mercado Demo LAYA'))
        product=db.scalar(select(Product).where(Product.business_id==business.id))
        address=db.scalar(select(Address).where(Address.user_id==customer.id))
        return customer.id,business.id,product.id,address.id,product.currency
    finally: db.close()

def test_health():
    r=client.get('/health'); assert r.status_code==200

def test_quote_is_server_calculated_and_in_coverage():
    _,bid,pid,aid,currency=seeded()
    r=client.post('/api/v1/checkout/quote',json={'business_id':bid,'items':[{'product_id':pid,'quantity':1}],'currency':currency,'delivery_method':'COURIER','address_id':aid})
    assert r.status_code==200,r.text
    data=r.json(); assert data['coverage'] is True; assert data['distance_km']>=0; assert data['delivery_fee']>=0; assert data['total']==data['subtotal']+data['delivery_fee']

def test_pickup_has_zero_delivery_fee():
    _,bid,pid,_,currency=seeded()
    r=client.post('/api/v1/checkout/quote',json={'business_id':bid,'items':[{'product_id':pid,'quantity':1}],'currency':currency,'delivery_method':'PICKUP','address_id':None})
    assert r.status_code==200,r.text
    assert r.json()['delivery_fee']==0

def test_order_ignores_client_delivery_price_and_uses_quote():
    _,bid,pid,aid,currency=seeded()
    payload={'business_id':bid,'items':[{'product_id':pid,'quantity':1}],'currency':currency,'delivery_method':'COURIER','address_id':aid,'payment_method':'SIMULATED','notes':'CI checkout'}
    q=client.post('/api/v1/checkout/quote',json=payload).json()
    r=client.post('/api/v1/checkout/order',json=payload)
    assert r.status_code==200,r.text
    data=r.json(); assert data['delivery_fee']==q['delivery_fee']; assert data['total']==q['total']
    db=SessionLocal()
    try: assert db.get(Order,data['id']) is not None
    finally: db.close()
