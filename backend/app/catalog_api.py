from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, delete, or_
from sqlalchemy.orm import Session
import cloudinary, cloudinary.uploader
from app.db import get_db
from app.models import Product, ProductImage, ProductPresentation, Business, User, Role
from app.schemas import PresentationIn, ProductIn
from app.security import require
from app.core.config import settings
router=APIRouter(prefix='/api/v1')

def owner_business(u,db):
    b=db.scalar(select(Business).where(Business.owner_id==u.id))
    if not b: raise HTTPException(404,'Negocio no encontrado')
    return b

def owner_product(pid,u,db):
    p=db.get(Product,pid)
    if not p: raise HTTPException(404,'Producto no encontrado')
    if u.role not in (Role.ADMIN,Role.SUPERADMIN):
        b=owner_business(u,db)
        if p.business_id!=b.id: raise HTTPException(403,'Producto fuera de tu comercio')
    return p

def presentation_dict(x): return {'id':x.id,'label':x.label,'amount':float(x.amount),'unit':x.unit,'price':float(x.price),'stock':x.stock,'active':x.active}
def rich_product(p,db):
    b=db.get(Business,p.business_id); imgs=db.scalars(select(ProductImage).where(ProductImage.product_id==p.id).order_by(ProductImage.order_index)).all(); pres=db.scalars(select(ProductPresentation).where(ProductPresentation.product_id==p.id).order_by(ProductPresentation.price)).all()
    return {'id':p.id,'business_id':p.business_id,'business_name':b.name if b else None,'business_type_id':b.business_type_id if b else None,'category_id':p.category_id,'name':p.name,'description':p.description,'image_url':p.image_url,'images':[{'id':x.id,'url':x.url,'order_index':x.order_index} for x in imgs],'price':float(p.price),'currency':p.currency,'stock':p.stock,'amount':float(p.amount),'unit':p.unit,'brand':p.brand,'sku':p.sku,'featured':p.featured,'active':p.active,'presentations':[presentation_dict(x) for x in pres]}

@router.get('/catalog/products')
def catalog_products(q:str|None=None,category_id:str|None=None,business_id:str|None=None,unit:str|None=None,featured:bool|None=None,db:Session=Depends(get_db)):
    stmt=select(Product).where(Product.active==True,Product.stock>0)
    if q: stmt=stmt.where(or_(Product.name.ilike(f'%{q}%'),Product.description.ilike(f'%{q}%'),Product.brand.ilike(f'%{q}%')))
    if category_id: stmt=stmt.where(Product.category_id==category_id)
    if business_id: stmt=stmt.where(Product.business_id==business_id)
    if unit: stmt=stmt.where(Product.unit==unit)
    if featured is not None: stmt=stmt.where(Product.featured==featured)
    return [rich_product(x,db) for x in db.scalars(stmt.order_by(Product.featured.desc(),Product.created_at.desc())).all()]

@router.get('/catalog/products/{pid}')
def catalog_product(pid:str,db:Session=Depends(get_db)):
    p=db.get(Product,pid)
    if not p: raise HTTPException(404,'Producto no encontrado')
    return rich_product(p,db)

@router.get('/merchant/catalog-products')
def merchant_catalog_products(u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=owner_business(u,db);return [rich_product(x,db) for x in db.scalars(select(Product).where(Product.business_id==b.id).order_by(Product.created_at.desc())).all()]

@router.post('/merchant/catalog-products')
def merchant_create_catalog_product(data:ProductIn,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    b=owner_business(u,db);p=Product(business_id=b.id,**data.model_dump());db.add(p);db.commit();db.refresh(p);return rich_product(p,db)

@router.put('/merchant/catalog-products/{pid}')
def merchant_update_catalog_product(pid:str,data:ProductIn,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    p=owner_product(pid,u,db)
    for k,v in data.model_dump().items(): setattr(p,k,v)
    db.commit();return rich_product(p,db)

@router.get('/products/{pid}/presentations')
def public_presentations(pid:str,db:Session=Depends(get_db)): return [presentation_dict(x) for x in db.scalars(select(ProductPresentation).where(ProductPresentation.product_id==pid,ProductPresentation.active==True)).all()]
@router.put('/merchant/products/{pid}/presentations')
def save_presentations(pid:str,items:list[PresentationIn],u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    owner_product(pid,u,db);db.execute(delete(ProductPresentation).where(ProductPresentation.product_id==pid))
    for x in items: db.add(ProductPresentation(product_id=pid,**x.model_dump()))
    db.commit();return {'ok':True,'items':[presentation_dict(x) for x in db.scalars(select(ProductPresentation).where(ProductPresentation.product_id==pid)).all()]}
@router.get('/products/{pid}/images')
def product_images(pid:str,db:Session=Depends(get_db)): return [{'id':x.id,'url':x.url,'order_index':x.order_index} for x in db.scalars(select(ProductImage).where(ProductImage.product_id==pid).order_by(ProductImage.order_index)).all()]
@router.post('/merchant/products/{pid}/images')
async def upload_product_image(pid:str,file:UploadFile=File(...),u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    p=owner_product(pid,u,db)
    if not settings.cloudinary_ready: raise HTTPException(503,'Cloudinary no está configurado. Completa las tres credenciales CLOUDINARY en backend/.env.')
    if not file.content_type or not file.content_type.startswith('image/'): raise HTTPException(400,'El archivo debe ser una imagen')
    raw=await file.read()
    if len(raw)>8*1024*1024: raise HTTPException(400,'La imagen supera 8 MB')
    cloudinary.config(cloud_name=settings.cloudinary_cloud_name,api_key=settings.cloudinary_api_key,api_secret=settings.cloudinary_api_secret,secure=True)
    result=cloudinary.uploader.upload(raw,folder=f'laya-market/products/{pid}',resource_type='image',transformation=[{'quality':'auto','fetch_format':'auto'}]);count=len(db.scalars(select(ProductImage).where(ProductImage.product_id==pid)).all());img=ProductImage(product_id=pid,url=result['secure_url'],public_id=result.get('public_id'),order_index=count);db.add(img)
    if not p.image_url:p.image_url=result['secure_url']
    db.commit();db.refresh(img);return {'id':img.id,'url':img.url,'order_index':img.order_index}
@router.delete('/merchant/products/{pid}/images/{iid}')
def delete_product_image(pid:str,iid:str,u:User=Depends(require(Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN)),db:Session=Depends(get_db)):
    p=owner_product(pid,u,db);img=db.get(ProductImage,iid)
    if not img or img.product_id!=pid:raise HTTPException(404,'Imagen no encontrada')
    if settings.cloudinary_ready and img.public_id:
        cloudinary.config(cloud_name=settings.cloudinary_cloud_name,api_key=settings.cloudinary_api_key,api_secret=settings.cloudinary_api_secret,secure=True);cloudinary.uploader.destroy(img.public_id)
    old=img.url;db.delete(img);db.flush()
    if p.image_url==old:
        nxt=db.scalar(select(ProductImage).where(ProductImage.product_id==pid).order_by(ProductImage.order_index));p.image_url=nxt.url if nxt else None
    db.commit();return {'ok':True}
