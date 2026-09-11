from math import radians, sin, cos, sqrt, atan2
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Address, Business, BusinessStatus, BusinessType, Category, Product, User, Role
from app.schemas import AddressIn
from app.security import current_user, require

router=APIRouter(prefix='/api/v1')

def distance_km(lat1,lon1,lat2,lon2):
    if None in (lat1,lon1,lat2,lon2): return None
    r=6371.0
    dlat=radians(lat2-lat1); dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return r*2*atan2(sqrt(a),sqrt(1-a))

def address_dict(a:Address):
    return {'id':a.id,'label':a.label,'line1':a.line1,'city':a.city,'province':a.province,'country':a.country,'postal_code':a.postal_code,'reference':a.reference,'latitude':a.latitude,'longitude':a.longitude,'is_default':a.is_default}

def product_view(p:Product,b:Business|None,c:Category|None,dist=None):
    return {'id':p.id,'business_id':p.business_id,'business_name':b.name if b else None,'business_type_id':b.business_type_id if b else None,'category_id':p.category_id,'category_name':c.name if c else None,'name':p.name,'description':p.description,'image_url':p.image_url,'price':float(p.price),'currency':p.currency,'stock':p.stock,'unit':p.unit,'amount':float(p.amount),'brand':p.brand,'sku':p.sku,'featured':p.featured,'distance_km':round(dist,2) if dist is not None else None}

@router.get('/search/products')
def search_products(q:str|None=None,category_id:str|None=None,business_type_id:str|None=None,business_id:str|None=None,unit:str|None=None,min_price:float|None=None,max_price:float|None=None,currency:str|None=None,featured:bool|None=None,country:str|None=None,lat:float|None=None,lng:float|None=None,max_distance_km:float|None=None,sort:str='recent',db:Session=Depends(get_db)):
    query=select(Product).where(Product.active==True,Product.stock>0)
    if q:
        term=f'%{q.strip()}%'; query=query.where(or_(Product.name.ilike(term),Product.description.ilike(term),Product.brand.ilike(term),Product.sku.ilike(term)))
    if category_id:
        ids=[category_id]+[x.id for x in db.scalars(select(Category).where(Category.parent_id==category_id)).all()]; query=query.where(Product.category_id.in_(ids))
    if business_id: query=query.where(Product.business_id==business_id)
    if unit: query=query.where(Product.unit==unit)
    if min_price is not None: query=query.where(Product.price>=min_price)
    if max_price is not None: query=query.where(Product.price<=max_price)
    if currency: query=query.where(Product.currency==currency)
    if featured is not None: query=query.where(Product.featured==featured)
    products=db.scalars(query.order_by(Product.created_at.desc())).all()
    bids={p.business_id for p in products}; businesses={b.id:b for b in db.scalars(select(Business).where(Business.id.in_(bids),Business.status==BusinessStatus.APPROVED)).all()} if bids else {}
    cats={c.id:c for c in db.scalars(select(Category).where(Category.id.in_({p.category_id for p in products}))).all()} if products else {}
    rows=[]
    for p in products:
        b=businesses.get(p.business_id)
        if not b: continue
        if business_type_id and b.business_type_id!=business_type_id: continue
        if country and b.country!=country: continue
        dist=distance_km(lat,lng,b.latitude,b.longitude) if lat is not None and lng is not None else None
        if max_distance_km is not None and dist is not None and dist>max_distance_km: continue
        rows.append(product_view(p,b,cats.get(p.category_id),dist))
    if sort=='price_asc': rows.sort(key=lambda x:x['price'])
    elif sort=='price_desc': rows.sort(key=lambda x:x['price'],reverse=True)
    elif sort=='distance': rows.sort(key=lambda x:x['distance_km'] if x['distance_km'] is not None else 999999)
    return rows

@router.get('/nearby/businesses')
def nearby_businesses(lat:float,lng:float,country:str|None=None,business_type_id:str|None=None,max_distance_km:float=30,db:Session=Depends(get_db)):
    q=select(Business).where(Business.status==BusinessStatus.APPROVED)
    if country:q=q.where(Business.country==country)
    if business_type_id:q=q.where(Business.business_type_id==business_type_id)
    types={x.id:x for x in db.scalars(select(BusinessType)).all()}
    out=[]
    for b in db.scalars(q).all():
        dist=distance_km(lat,lng,b.latitude,b.longitude)
        if dist is not None and dist<=max_distance_km:
            t=types.get(b.business_type_id)
            out.append({'id':b.id,'name':b.name,'description':b.description,'logo_url':b.logo_url,'country':b.country,'city':b.city,'latitude':b.latitude,'longitude':b.longitude,'delivery_radius_km':b.delivery_radius_km,'distance_km':round(dist,2),'in_delivery_zone':dist<=b.delivery_radius_km,'business_type_id':b.business_type_id,'business_type_name':t.name if t else None,'own_delivery':b.own_delivery,'courier_enabled':b.courier_enabled})
    out.sort(key=lambda x:x['distance_km'])
    return out

@router.get('/addresses')
def list_addresses(u:User=Depends(current_user),db:Session=Depends(get_db)):
    return [address_dict(x) for x in db.scalars(select(Address).where(Address.user_id==u.id).order_by(Address.is_default.desc(),Address.label)).all()]

@router.post('/addresses')
def create_address(data:AddressIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    if data.is_default:
        for x in db.scalars(select(Address).where(Address.user_id==u.id)).all(): x.is_default=False
    a=Address(user_id=u.id,**data.model_dump());db.add(a);db.commit();db.refresh(a);return address_dict(a)

@router.put('/addresses/{aid}')
def update_address(aid:str,data:AddressIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    a=db.get(Address,aid)
    if not a or a.user_id!=u.id: raise HTTPException(404,'Dirección no encontrada')
    if data.is_default:
        for x in db.scalars(select(Address).where(Address.user_id==u.id,Address.id!=aid)).all(): x.is_default=False
    for k,v in data.model_dump().items():setattr(a,k,v)
    db.commit();return address_dict(a)

@router.delete('/addresses/{aid}')
def delete_address(aid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    a=db.get(Address,aid)
    if not a or a.user_id!=u.id: raise HTTPException(404,'Dirección no encontrada')
    db.delete(a);db.commit();return {'ok':True}

@router.patch('/merchant/business/location')
def merchant_business_location(latitude:float,longitude:float,delivery_radius_km:float=8,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=db.scalar(select(Business).where(Business.owner_id==u.id))
    if not b: raise HTTPException(404,'Negocio no encontrado')
    b.latitude=latitude;b.longitude=longitude;b.delivery_radius_km=max(0.5,min(delivery_radius_km,100));db.commit()
    return {'ok':True,'latitude':b.latitude,'longitude':b.longitude,'delivery_radius_km':b.delivery_radius_km}
