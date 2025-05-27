from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.ingredient import Ingredient
from app.dependencies.auth import role_required
from fastapi import HTTPException
from app.schemas.inventory import LowStockItem, IngredientUpdate
from app.schemas.inventory import IngredientOut


router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/low-stock", response_model=list[LowStockItem], dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_low_stock_items(db: AsyncSession = Depends(get_db)):
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

@router.patch("/{ingredient_id}", dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()

    if not ingredient:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı.")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(ingredient, field, value)

    await db.commit()
    await db.refresh(ingredient)
    return ingredient

@router.get("/", response_model=list[IngredientOut], dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_all_ingredients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ingredient))
    return result.scalars().all()

@router.get("/{ingredient_id}", response_model=IngredientOut, dependencies=[Depends(role_required(["MANAGER", "KITCHEN"]))])
async def get_ingredient_by_id(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()

    if not ingredient:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı.")

    return ingredient
