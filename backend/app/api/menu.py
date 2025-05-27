from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemOut
from app.core.database import get_db

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("/", response_model=list[MenuItemOut])
async def get_menu(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MenuItem))
    items = result.scalars().all()
    return items

from app.schemas.menu import MenuItemCreate

@router.post("/", response_model=MenuItemOut)
async def create_menu_item(
    payload: MenuItemCreate,
    db: AsyncSession = Depends(get_db)
):
    item = MenuItem(**payload.dict())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

from app.schemas.menu import MenuItemUpdate
from fastapi import HTTPException

@router.patch("/{item_id}", response_model=MenuItemOut)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menü öğesi bulunamadı.")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item
