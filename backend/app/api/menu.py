from fastapi import APIRouter, Depends, HTTPException # Tekrar eden importlar birleştirildi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session
from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemOut, MenuItemCreate, MenuItemUpdate # Tüm şemalar tek yerden import edildi

router = APIRouter(prefix="/menu", tags=["menu"])

# Menüdeki tüm ürünleri getir (sadece mevcut olanlar)
@router.get("/", response_model=list[MenuItemOut])
async def get_menu_items(db: AsyncSession = Depends(get_async_session)):
    # is_available flag'i, malzeme stok durumuna göre otomatik olarak güncelleniyor.
    # Bu endpoint sadece aktif/mevcut menü öğelerini döndürür.
    menu_items_result = await db.execute(
        select(MenuItem).where(MenuItem.is_available == True)
    )
    menu_items = menu_items_result.scalars().all()
    return menu_items

# Yeni menü öğesi oluştur
@router.post("/", response_model=MenuItemOut)
async def create_menu_item(
    payload: MenuItemCreate,
    session: AsyncSession = Depends(get_async_session)
):
    # Yeni menü öğesi varsayılan olarak mevcut (is_available=True) olarak başlar.
    # Malzeme eklenirse ve stok yetersizse, check_and_update_menu_item_availability daha sonra onu pasif yapabilir.
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

# Menü öğesi silme (İsteğe bağlı olarak eklenebilir)
# @router.delete("/{item_id}", status_code=204)
# async def delete_menu_item(
#     item_id: int,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
#     item = result.scalar_one_or_none()

#     if not item:
#         raise HTTPException(status_code=404, detail="Menü öğesi bulunamadı.")

#     await session.delete(item)
#     await session.commit()
#     return Response(status_code=204)