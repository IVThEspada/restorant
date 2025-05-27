from fastapi import FastAPI
import asyncio
from app.api import menu
from app.core.database import engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemOut
from app.core.database import get_db
from app.models import user
from app.models import ingredient, menu_item_ingredient


app = FastAPI(
    title="Restaurant API",
    root_path="/",
    redirect_slashes=True,
    swagger_ui_init_oauth={},  # ← ekle
    openapi_tags=[  # optional, kategori görünümü için
        {"name": "auth", "description": "Login işlemleri"},
        {"name": "orders", "description": "Sipariş işlemleri"},
        {"name": "inventory", "description": "Stok yönetimi"},
    ]
)

from fastapi.openapi.utils import get_openapi

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
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


app.include_router(menu.router)

@app.get("/testmenu", response_model=list[MenuItemOut])
async def get_menu_test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MenuItem))
    return result.scalars().all()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from app.api import orders
app.include_router(orders.router)

from app.api import kitchen
app.include_router(kitchen.router)

from app.api import table
app.include_router(table.router)

from app.api import auth
app.include_router(auth.router)

from app.api import inventory
app.include_router(inventory.router)

from app.api import schedule
app.include_router(schedule.router)






