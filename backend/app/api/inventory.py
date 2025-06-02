from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient # Yeni import
from app.dependencies.auth import role_required
from app.schemas.inventory import LowStockItem, IngredientUpdate, IngredientOut
from app.services.menu_service import check_and_update_menu_item_availability # Yeni import

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/low-stock", response_model=list[LowStockItem], dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_low_stock_items(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(Ingredient).where(Ingredient.stock_quantity < Ingredient.low_stock_threshold)
    )
    low_stock_items = result.scalars().all()

    return [
        LowStockItem(
            name=item.name,
            stock_quantity=item.stock_quantity,
            low_stock_threshold=item.low_stock_threshold
        )
        for item in low_stock_items
    ]


@router.patch("/{ingredient_id}", response_model=IngredientOut,
              dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])  # response_model ekledim
async def update_ingredient(
        ingredient_id: int,
        payload: IngredientUpdate,
        db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()

    if not ingredient:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı.")

    # Stok değişmeden önceki değerini kaydedelim
    old_stock_quantity = ingredient.stock_quantity

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(ingredient, field, value)

    # Değişiklikleri veritabanına kaydetmeden önce (veya sonra) ilgili menü öğelerini bulup güncellemeliyiz.
    # Buradaki db.commit() çağrısı, ingredient değişikliğini commit eder.
    await db.commit()
    await db.refresh(ingredient)

    # Stok miktarında bir değişiklik olduysa veya herhangi bir güncelleme varsa
    # bu malzemeyi kullanan tüm menü öğelerinin uygunluğunu kontrol et
    # (Sadece `stock_quantity` değiştiyse kontrol etmek daha verimli olabilir)
    if 'stock_quantity' in payload.dict(exclude_unset=True) and old_stock_quantity != ingredient.stock_quantity:
        print(
            f"DEBUG: Malzeme '{ingredient.name}' stoğu {old_stock_quantity} -> {ingredient.stock_quantity} olarak değişti. İlgili menü öğeleri kontrol ediliyor.")

        menu_items_using_this_ingredient_result = await db.execute(
            select(MenuItemIngredient.menu_item_id)
            .where(MenuItemIngredient.ingredient_id == ingredient.id)
        )
        menu_item_ids = menu_items_using_this_ingredient_result.scalars().all()

        for mi_id in set(menu_item_ids):  # Tekrar eden ID'leri önlemek için set kullan
            await check_and_update_menu_item_availability(db, mi_id)

        # Not: check_and_update_menu_item_availability fonksiyonu kendi içinde commit yaptığı için
        # burada tekrar db.commit() çağırmaya gerek yok.

    return ingredient

@router.get("/", response_model=list[IngredientOut], dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_all_ingredients(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Ingredient))
    return result.scalars().all()

@router.get("/{ingredient_id}", response_model=IngredientOut, dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_ingredient_by_id(
    ingredient_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()

    if not ingredient:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı.")

    return ingredient
