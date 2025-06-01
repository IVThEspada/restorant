from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemOut, MenuItemCreate, MenuItemUpdate
from app.core.database import get_async_session

router = APIRouter(prefix="/menu", tags=["menu"])

# Menüdeki tüm ürünleri getir
@router.get("/", response_model=list[MenuItemOut])
async def get_menu(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(MenuItem))
    items = result.scalars().all()
    return items

# Yeni menü öğesi oluştur
@router.post("/", response_model=MenuItemOut)
async def create_menu_item(
    payload: MenuItemCreate,
    session: AsyncSession = Depends(get_async_session)
):
    item = MenuItem(**payload.dict())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

# Menü öğesi güncelle
@router.patch("/{item_id}", response_model=MenuItemOut)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menü öğesi bulunamadı.")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(item, field, value)

    await session.commit()
    await session.refresh(item)
    return item
