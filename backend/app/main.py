from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router
from app.catalog_api import router as catalog_router
from app.geo_api import router as geo_router
from app.checkout_api import router as checkout_router
from app.order_ops_api import router as order_ops_router
from app.logistics_api import router as logistics_router
from app.whatsapp_api import ops_router as whatsapp_ops_router, router as whatsapp_router

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(logistics_router)
app.include_router(router)
app.include_router(catalog_router)
app.include_router(geo_router)
app.include_router(checkout_router)
app.include_router(order_ops_router)
app.include_router(whatsapp_router)
app.include_router(whatsapp_ops_router)

@app.get("/")
def root(): return {"name":"LAYA Market API","docs":"/docs"}
@app.get("/health")
def health(): return {"status":"ok","service":"LAYA API"}
