from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models import User, Role

pwd=CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2=OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login', auto_error=False)

def hash_password(v:str): return pwd.hash(v)
def verify_password(v:str,h:str): return pwd.verify(v,h)
def make_token(user:User):
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({'sub':user.id,'role':user.role.value,'exp':exp},settings.jwt_secret,algorithm=settings.jwt_algorithm)

def _decode_user(token:str|None, db:Session):
    if not token:
        return None
    try:
        data=jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm])
        uid=data['sub']
    except (JWTError, KeyError):
        raise HTTPException(401,'Token inválido')
    user=db.get(User,uid)
    if not user:
        raise HTTPException(401,'Usuario inexistente')
    return user

def _preview_user(db:Session, roles:tuple[Role,...]):
    for role in roles:
        user=db.scalar(select(User).where(User.role==role))
        if user:
            return user
    return None

def current_user(token:str|None=Depends(oauth2), db:Session=Depends(get_db)):
    user=_decode_user(token,db)
    if user:
        return user
    if settings.env.lower()=='development':
        preview=_preview_user(db,(Role.CUSTOMER,Role.MERCHANT,Role.ADMIN,Role.SUPERADMIN))
        if preview:
            return preview
    raise HTTPException(401,'Autenticación requerida')

def require(*roles:Role):
    def dep(token:str|None=Depends(oauth2), db:Session=Depends(get_db)):
        user=_decode_user(token,db)
        if user:
            if user.role not in roles:
                raise HTTPException(403,'No autorizado')
            return user
        if settings.env.lower()=='development':
            preview=_preview_user(db,roles)
            if preview:
                return preview
        raise HTTPException(401,'Autenticación requerida')
    return dep
