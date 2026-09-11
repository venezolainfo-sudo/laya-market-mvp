from math import radians, sin, cos, sqrt, atan2
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Address, Business, BusinessStatus, Product, ProductPresentation


def distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    r=6371.0
    dlat=radians(lat2-lat1); dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return r*2*atan2(sqrt(a),sqrt(1-a))


def resolve_cart(db:Session,business_id:str,items,currency:str,lock:bool=False):
    b=db.get(Business,business_id)
    if not b or b.status!=BusinessStatus.APPROVED:
        raise HTTPException(400,'Comercio no disponible')
    if not items:
        raise HTTPException(400,'El carrito está vacío')
    resolved=[]; subtotal=0.0
    for item in items:
        q=select(Product).where(Product.id==item.product_id)
        if lock:q=q.with_for_update()
        p=db.scalar(q)
        if not p or not p.active or p.business_id!=b.id:
            raise HTTPException(400,'Producto inválido o fuera del comercio')
        if p.currency!=currency:
            raise HTTPException(400,'Todos los productos deben usar la moneda del pedido')
        price=float(p.price); stock=p.stock; presentation=None
        if item.presentation_id:
            pq=select(ProductPresentation).where(ProductPresentation.id==item.presentation_id)
            if lock:pq=pq.with_for_update()
            presentation=db.scalar(pq)
            if not presentation or presentation.product_id!=p.id or not presentation.active:
                raise HTTPException(400,f'Presentación inválida: {p.name}')
            price=float(presentation.price); stock=presentation.stock
        if stock<item.quantity:
            raise HTTPException(400,f'Stock insuficiente: {p.name}')
        line=round(price*item.quantity,2); subtotal+=line
        resolved.append({'product':p,'presentation':presentation,'quantity':item.quantity,'unit_price':price,'subtotal':line})
    return b,resolved,round(subtotal,2)


def quote_checkout(db:Session,user,business_id:str,items,currency:str,delivery_method:str,address_id:str|None,lock:bool=False):
    b,resolved,subtotal=resolve_cart(db,business_id,items,currency,lock)
    if delivery_method=='PICKUP':
        if not b.pickup_enabled:
            raise HTTPException(400,'Este comercio no ofrece retiro')
        return {'business':b,'resolved':resolved,'address':None,'subtotal':subtotal,'delivery_fee':0.0,'total':subtotal,'distance_km':0.0,'coverage':True,'delivery_method':'PICKUP'}
    if delivery_method=='OWN_DELIVERY' and not b.own_delivery:
        raise HTTPException(400,'Este comercio no ofrece entrega propia')
    if delivery_method=='COURIER' and not b.courier_enabled:
        raise HTTPException(400,'Este comercio no admite cadete LAYA')
    if not address_id:
        raise HTTPException(400,'Selecciona una dirección de entrega')
    a=db.get(Address,address_id)
    if not a or a.user_id!=user.id:
        raise HTTPException(404,'Dirección no encontrada')
    if None in (a.latitude,a.longitude):
        raise HTTPException(400,'La dirección necesita ubicación en el mapa')
    if None in (b.latitude,b.longitude):
        raise HTTPException(400,'El comercio todavía no configuró su ubicación')
    if a.country!=b.country:
        raise HTTPException(400,'La dirección está en otro país')
    dist=distance_km(b.latitude,b.longitude,a.latitude,a.longitude)
    if dist is None:
        raise HTTPException(400,'No se pudo calcular la distancia')
    if dist>b.delivery_radius_km:
        raise HTTPException(400,f'Fuera de cobertura. Distancia {dist:.1f} km; radio máximo {b.delivery_radius_km:.1f} km')
    fee=max(float(b.delivery_min_fee),float(b.delivery_base_fee)+float(b.delivery_per_km)*dist)
    fee=round(fee,2); total=round(subtotal+fee,2)
    return {'business':b,'resolved':resolved,'address':a,'subtotal':subtotal,'delivery_fee':fee,'total':total,'distance_km':round(dist,2),'coverage':True,'delivery_method':delivery_method}
