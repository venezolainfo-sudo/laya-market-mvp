from sqlalchemy import select
from app.db import SessionLocal
from app.models import *
from app.security import hash_password

def ensure_taxonomy(db):
    specs=[('Supermercados','supermercados','🛒'),('Restaurantes','restaurantes','🍽️'),('Pizzerías','pizzerias','🍕'),('Farmacias','farmacias','💊'),('Panaderías','panaderias','🥖'),('Tiendas','tiendas','🏪'),('Mascotas','mascotas','🐾'),('Otros','otros','◈')]
    types={}
    for i,(name,slug,icon) in enumerate(specs):
        x=db.scalar(select(BusinessType).where(BusinessType.slug==slug))
        if not x:x=BusinessType(name=name,slug=slug,icon=icon,order_index=i);db.add(x);db.flush()
        types[slug]=x
    cats=[('Almacén','almacen','🛒','supermercados',[('Arroz y granos','arroz-granos','🌾'),('Pastas','pastas','🍝'),('Aceites y condimentos','aceites-condimentos','🫙'),('Enlatados','enlatados','🥫')]),('Bebidas','bebidas','🥤','supermercados',[('Agua','agua','💧'),('Gaseosas','gaseosas','🥤'),('Jugos','jugos','🧃')]),('Limpieza','limpieza','🧹','supermercados',[('Hogar','limpieza-hogar','🧽'),('Lavandería','lavanderia','🧺')]),('Panificados','panificados','🥖','panaderias',[('Pan','pan','🥖'),('Facturas y dulces','facturas-dulces','🥐'),('Pre-pizzas','pre-pizzas','🍕')]),('Comidas','comidas','🍽️','restaurantes',[('Entradas','entradas','🥗'),('Platos principales','platos-principales','🍲'),('Postres','postres','🍰')]),('Pizzas','pizzas','🍕','pizzerias',[('Pizzas clásicas','pizzas-clasicas','🍕'),('Pizzas especiales','pizzas-especiales','🍕'),('Combos','combos-pizzeria','🥤')]),('Farmacia','farmacia','💊','farmacias',[('Cuidado personal','cuidado-personal','🧴'),('Higiene','higiene','🧼'),('Primeros auxilios','primeros-auxilios','🩹')]),('Mascotas','mascotas','🐾','mascotas',[('Alimentos','alimentos-mascotas','🦴'),('Higiene y cuidado','higiene-mascotas','🐾'),('Accesorios','accesorios-mascotas','🦮')])]
    for order,(name,slug,icon,bt_slug,subs) in enumerate(cats):
        root=db.scalar(select(Category).where(Category.slug==slug))
        if not root:root=Category(name=name,slug=slug,icon=icon,business_type_id=types[bt_slug].id,order_index=order);db.add(root);db.flush()
        elif not root.business_type_id:root.business_type_id=types[bt_slug].id
        for j,(sn,ss,si) in enumerate(subs):
            if not db.scalar(select(Category).where(Category.slug==ss)):db.add(Category(name=sn,slug=ss,icon=si,parent_id=root.id,business_type_id=types[bt_slug].id,order_index=j))
    db.flush();return types

def configure_demo(db,types):
    for b in db.scalars(select(Business)).all():
        if not b.business_type_id:b.business_type_id=types['supermercados'].id
        if b.name=='Mercado Demo LAYA' and b.country=='AR':
            if b.latitude is None:b.latitude=-32.8895;b.longitude=-68.8458
            b.delivery_radius_km=12;b.delivery_base_fee=1800;b.delivery_per_km=220;b.delivery_min_fee=2200;b.pickup_enabled=True;b.own_delivery=True;b.courier_enabled=True
    customer=db.scalar(select(User).where(User.email=='cliente@layamarket.local'))
    if customer:
        if not customer.phone:customer.phone='+54 261 0000000'
        if not db.scalar(select(Address).where(Address.user_id==customer.id)):
            db.add(Address(user_id=customer.id,label='Casa',line1='Centro, Mendoza',city='Mendoza',province='Mendoza',country='AR',latitude=-32.8908,longitude=-68.8272,is_default=True))

def run():
    db=SessionLocal()
    try:
        types=ensure_taxonomy(db)
        admin=db.scalar(select(User).where(User.email=='admin@layamarket.local'))
        if admin:
            configure_demo(db,types);db.commit();print('Taxonomía, cobertura y checkout LAYA Market actualizados');return
        admin=User(email='admin@layamarket.local',password_hash=hash_password('Admin123!'),name='Administración LAYA',role=Role.ADMIN,country='AR');merchant=User(email='comercio@layamarket.local',password_hash=hash_password('Comercio123!'),name='Comercio Demo',role=Role.MERCHANT,country='AR');customer=User(email='cliente@layamarket.local',password_hash=hash_password('Cliente123!'),name='Cliente Demo',phone='+54 261 0000000',role=Role.CUSTOMER,country='AR');db.add_all([admin,merchant,customer]);db.flush()
        b=Business(owner_id=merchant.id,business_type_id=types['supermercados'].id,name='Mercado Demo LAYA',description='Productos cotidianos con entrega a domicilio.',country='AR',city='Mendoza',address='Zona demo',latitude=-32.8895,longitude=-68.8458,delivery_radius_km=12,delivery_base_fee=1800,delivery_per_km=220,delivery_min_fee=2200,pickup_enabled=True,status=BusinessStatus.APPROVED,own_delivery=True,courier_enabled=True);db.add(b);db.flush()
        db.add(Address(user_id=customer.id,label='Casa',line1='Centro, Mendoza',city='Mendoza',province='Mendoza',country='AR',latitude=-32.8908,longitude=-68.8272,is_default=True))
        cat=db.scalar(select(Category).where(Category.slug=='panificados'));p=Product(business_id=b.id,category_id=cat.id,name='Pan casero',description='Producto fresco preparado para entrega local.',image_url='https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800',price=3500,currency='ARS',stock=20,unit='unidad',featured=True);db.add(p);db.flush();db.add_all([ProductPresentation(product_id=p.id,label='1 unidad',amount=1,unit='unidad',price=3500,stock=20),ProductPresentation(product_id=p.id,label='Pack x6',amount=6,unit='unidad',price=19000,stock=5),Courier(name='Cadete Demo 1',phone='+54 261 0000001',country='AR',city='Mendoza'),Courier(name='Cadete Demo 2',phone='+54 261 0000002',country='AR',city='Mendoza')]);db.commit();print('Seed aplicado correctamente')
    finally:db.close()
if __name__=='__main__':run()
