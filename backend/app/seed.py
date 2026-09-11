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
    cats=[
      ('Almacén','almacen','🛒','supermercados',[('Arroz y granos','arroz-granos','🌾'),('Pastas','pastas','🍝'),('Aceites y condimentos','aceites-condimentos','🫙'),('Enlatados','enlatados','🥫')]),
      ('Bebidas','bebidas','🥤','supermercados',[('Agua','agua','💧'),('Gaseosas','gaseosas','🥤'),('Jugos','jugos','🧃')]),
      ('Limpieza','limpieza','🧹','supermercados',[('Hogar','limpieza-hogar','🧽'),('Lavandería','lavanderia','🧺')]),
      ('Panificados','panificados','🥖','panaderias',[('Pan','pan','🥖'),('Facturas y dulces','facturas-dulces','🥐'),('Pre-pizzas','pre-pizzas','🍕')]),
      ('Comidas','comidas','🍽️','restaurantes',[('Entradas','entradas','🥗'),('Platos principales','platos-principales','🍲'),('Postres','postres','🍰')]),
      ('Pizzas','pizzas','🍕','pizzerias',[('Pizzas clásicas','pizzas-clasicas','🍕'),('Pizzas especiales','pizzas-especiales','🍕'),('Combos','combos-pizzeria','🥤')]),
      ('Farmacia','farmacia','💊','farmacias',[('Cuidado personal','cuidado-personal','🧴'),('Higiene','higiene','🧼'),('Primeros auxilios','primeros-auxilios','🩹')]),
      ('Mascotas','mascotas','🐾','mascotas',[('Alimentos','alimentos-mascotas','🦴'),('Higiene y cuidado','higiene-mascotas','🐾'),('Accesorios','accesorios-mascotas','🦮')])]
    for order,(name,slug,icon,bt_slug,subs) in enumerate(cats):
        root=db.scalar(select(Category).where(Category.slug==slug))
        if not root:
            root=Category(name=name,slug=slug,icon=icon,business_type_id=types[bt_slug].id,order_index=order);db.add(root);db.flush()
        elif not root.business_type_id:root.business_type_id=types[bt_slug].id
        for j,(sn,ss,si) in enumerate(subs):
            sub=db.scalar(select(Category).where(Category.slug==ss))
            if not sub:db.add(Category(name=sn,slug=ss,icon=si,parent_id=root.id,business_type_id=types[bt_slug].id,order_index=j))
    db.flush();return types

def run():
    db=SessionLocal()
    try:
        types=ensure_taxonomy(db)
        admin=db.scalar(select(User).where(User.email=='admin@layamarket.local'))
        if admin:
            for b in db.scalars(select(Business)).all():
                if not b.business_type_id:b.business_type_id=types['supermercados'].id
                if b.name=='Mercado Demo LAYA' and b.country=='AR' and b.latitude is None:
                    b.latitude=-32.8895;b.longitude=-68.8458;b.delivery_radius_km=12
            db.commit();print('Taxonomía y geolocalización LAYA Market actualizadas');return
        admin=User(email='admin@layamarket.local',password_hash=hash_password('Admin123!'),name='Administración LAYA',role=Role.ADMIN,country='AR');merchant=User(email='comercio@layamarket.local',password_hash=hash_password('Comercio123!'),name='Comercio Demo',role=Role.MERCHANT,country='AR');customer=User(email='cliente@layamarket.local',password_hash=hash_password('Cliente123!'),name='Cliente Demo',role=Role.CUSTOMER,country='AR');db.add_all([admin,merchant,customer]);db.flush()
        b=Business(owner_id=merchant.id,business_type_id=types['supermercados'].id,name='Mercado Demo LAYA',description='Productos cotidianos con entrega a domicilio.',country='AR',city='Mendoza',address='Zona demo',latitude=-32.8895,longitude=-68.8458,delivery_radius_km=12,status=BusinessStatus.APPROVED,own_delivery=True,courier_enabled=True);db.add(b);db.flush()
        cat=db.scalar(select(Category).where(Category.slug=='panificados'));imgs=['https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800'];db.add(Product(business_id=b.id,category_id=cat.id,name='Pan casero',description='Producto fresco preparado para entrega local.',image_url=imgs[0],price=3500,currency='ARS',stock=20,unit='unidad'));db.add_all([Courier(name='Cadete Demo 1',phone='+54 261 0000001',country='AR',city='Mendoza'),Courier(name='Cadete Demo 2',phone='+54 261 0000002',country='AR',city='Mendoza')]);db.commit();print('Seed aplicado correctamente')
    finally:db.close()
if __name__=='__main__':run()
