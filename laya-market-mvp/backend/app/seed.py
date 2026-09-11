from sqlalchemy import select
from app.db import SessionLocal
from app.models import *
from app.security import hash_password

def run():
    db=SessionLocal()
    try:
        if db.scalar(select(User).where(User.email=='admin@layamarket.local')): print('Seed ya aplicado'); return
        admin=User(email='admin@layamarket.local',password_hash=hash_password('Admin123!'),name='Administración LAYA',role=Role.ADMIN,country='AR')
        merchant=User(email='comercio@layamarket.local',password_hash=hash_password('Comercio123!'),name='Comercio Demo',role=Role.MERCHANT,country='AR')
        customer=User(email='cliente@layamarket.local',password_hash=hash_password('Cliente123!'),name='Cliente Demo',role=Role.CUSTOMER,country='AR')
        db.add_all([admin,merchant,customer]);db.flush()
        cats=[Category(name='Panificados',slug='panificados',icon='🥖'),Category(name='Pastas',slug='pastas',icon='🍝'),Category(name='Pre-pizzas',slug='pre-pizzas',icon='🍕'),Category(name='Milanesas',slug='milanesas',icon='🥩'),Category(name='Almacén',slug='almacen',icon='🛒'),Category(name='Limpieza',slug='limpieza',icon='🧹')]
        db.add_all(cats);db.flush()
        b=Business(owner_id=merchant.id,name='Mercado Demo LAYA',description='Productos cotidianos con entrega a domicilio.',country='AR',city='Mendoza',address='Zona demo',status=BusinessStatus.APPROVED,own_delivery=True,courier_enabled=True)
        db.add(b);db.flush()
        imgs=['https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800','https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=800','https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800','https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800']
        prods=[('Pan casero',cats[0],3500,'ARS',20,imgs[0]),('Pasta fresca',cats[1],5200,'ARS',15,imgs[1]),('Pre-pizza artesanal',cats[2],4000,'ARS',18,imgs[2]),('Milanesas x kg',cats[3],9.5,'USD',12,imgs[3])]
        for n,c,p,cur,s,img in prods: db.add(Product(business_id=b.id,category_id=c.id,name=n,description='Producto fresco preparado para entrega local.',image_url=img,price=p,currency=cur,stock=s,unit='unidad'))
        db.add_all([Courier(name='Cadete Demo 1',phone='+54 261 0000001',country='AR',city='Mendoza'),Courier(name='Cadete Demo 2',phone='+54 261 0000002',country='AR',city='Mendoza')])
        db.commit();print('Seed aplicado correctamente')
    finally: db.close()
if __name__=='__main__': run()
