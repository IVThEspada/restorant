from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session
from app.models.user import User
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.table import DiningTable
from app.models.schedule import Schedule
from app.api.auth import get_current_user

router = APIRouter(prefix="/manager", tags=["Manager"])


@router.get("/menu")
async def get_menu(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(MenuItem))
    items = result.scalars().all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "price": float(item.price),  # Numeric ise float() ile dönüşüm yap
            "is_available": item.is_available,
            "img_url": item.img_url,
            "tags": item.tags,
            "allergens": item.allergens
        }
        for item in items
    ]


@router.get("/tables")
async def get_tables(session: AsyncSession = Depends(get_async_session)):
    tables = await session.execute(select(DiningTable))
    table_objs = tables.scalars().all()

    return [
        {
            "id": t.id,
            "number": t.number,
            "status": t.status.value,
            "current_user_id": t.current_user_id
        }
        for t in table_objs
    ]



@router.get("/protected-dashboard")
async def get_protected_dashboard(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "MANAGER":
        raise HTTPException(status_code=403, detail="Access denied")

    users = await session.execute(select(User))
    ingredients = await session.execute(select(Ingredient))
    schedules = await session.execute(select(Schedule))

    return {
        "users": [dict(row._mapping) for row in users.fetchall()],
        "ingredients": [dict(row._mapping) for row in ingredients.fetchall()],
        "schedules": [dict(row._mapping) for row in schedules.fetchall()],
    }


@router.get("/dashboard")
async def get_dashboard_data(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "MANAGER":
        raise HTTPException(status_code=403, detail="Access denied")

    users = await session.execute(select(User))
    menu_items = await session.execute(select(MenuItem))
    ingredients = await session.execute(select(Ingredient))
    tables = await session.execute(select(DiningTable))
    schedules = await session.execute(select(Schedule))

    return {
        "users": [dict(row._mapping) for row in users.fetchall()],
        "menu_items": [dict(row._mapping) for row in menu_items.fetchall()],
        "ingredients": [dict(row._mapping) for row in ingredients.fetchall()],
        "tables": [dict(row._mapping) for row in tables.fetchall()],
        "schedules": [dict(row._mapping) for row in schedules.fetchall()],
    }
