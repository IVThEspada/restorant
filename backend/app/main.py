from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api import customer
from app.core.database import engine, Base, get_async_session
from app.schemas.menu import MenuItemOut
from app.models.menu_item import MenuItem

# FastAPI uygulaması
app = FastAPI(
    title="Restaurant API",
    root_path="/",
    redirect_slashes=True,
    swagger_ui_init_oauth={},
    openapi_tags=[
        {"name": "auth", "description": "Login işlemleri"},
        {"name": "orders", "description": "Sipariş işlemleri"},
        {"name": "inventory", "description": "Stok yönetimi"},
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAPI JWT yapılandırması
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Restaurant API",
        version="1.0.0",
        description="Simple token auth system for roles",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    # AŞAĞIDAKİ DÖNGÜYÜ KALDIRIN!
    # for path in openapi_schema["paths"].values():
    #     for method in path.values():
    #         method["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Başlangıçta tabloları oluştur
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Test endpoint
@app.get("/testmenu", response_model=list[MenuItemOut])
async def get_menu_test(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(MenuItem))
    return result.scalars().all()

# Tüm router'lar
from app.api import (
    auth,
    menu,
    orders,
    kitchen,
    table,
    inventory,
    schedule,
    manager
)

app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(kitchen.router)
app.include_router(table.router)
app.include_router(inventory.router)
app.include_router(schedule.router)
app.include_router(manager.router)
app.include_router(customer.router)
