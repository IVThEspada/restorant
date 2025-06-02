from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session
from app.models.order import Order, OrderStatus, OrderItem
from app.models.menu_item import MenuItem
from app.models.table import DiningTable, TableStatus
from app.schemas.order import (
    OrderCreate, OrderOut, OrderItemOut, OrderSummary,
    OrderItemSummary, OrderPaymentUpdate, OrderUpdate
)
from app.schemas.order import OrderItemUpdate
from app.dependencies.auth import get_current_user, role_required
from app.models.user import User
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient
from app.services.menu_service import check_and_update_menu_item_availability # Yeni import

router = APIRouter(prefix="/orders", tags=["orders"])


# ✅ SIPARIŞ VER (CUSTOMER rolü)
@router.post("/", response_model=OrderOut, dependencies=[Depends(role_required(["CUSTOMER"]))])
async def place_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    table_result = await db.execute(select(DiningTable).where(DiningTable.id == payload.table_id))
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")
    if table.status in [TableStatus.CLOSED, TableStatus.RESERVED]:
        raise HTTPException(status_code=400, detail=f"Masa şu anda uygun değil. (Durum: {table.status.value})")
    if table.current_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu masada oturmuyorsunuz!")

    # Menü ürünleri
    menu_stmt = select(MenuItem).where(MenuItem.id.in_([i.menu_item_id for i in payload.items]))
    result = await db.execute(menu_stmt)
    menu_items = {m.id: m for m in result.scalars().all()}

    # Ürün kontrol
    for item in payload.items:
        mi = menu_items.get(item.menu_item_id)
        if not mi:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: id={item.menu_item_id}")
        if not mi.is_available:
            raise HTTPException(status_code=400, detail=f"'{mi.name}' ürünü şu anda siparişe kapalı.")

        # ✅ Yeni sipariş oluştur
        order = Order(
            table_id=payload.table_id,
            customer_id=current_user.id
        )
        db.add(order)
        await db.flush()  # order.id'ye erişmek için flush

        # Sipariş ürünleri ekle
        for item in payload.items:
            db.add(OrderItem(
                order_id=order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                note=item.note
            ))

        # Stok güncelle ve menü öğesi uygunluğunu kontrol et
        menu_items_to_check_availability = set()  # Tekrar eden kontrolleri önlemek için set
        for item in payload.items:
            ingredient_result = await db.execute(
                select(MenuItemIngredient).where(MenuItemIngredient.menu_item_id == item.menu_item_id)
            )
            used_ingredients = ingredient_result.scalars().all()

            for usage in used_ingredients:
                ingredient_result = await db.execute(
                    select(Ingredient).where(Ingredient.id == usage.ingredient_id)
                )
                ingredient = ingredient_result.scalar_one_or_none()
                if ingredient:
                    ingredient.stock_quantity -= usage.amount_used * item.quantity
                    db.add(ingredient)  # Değişikliği session'a ekle

            menu_items_to_check_availability.add(item.menu_item_id)  # Bu menü öğesinin stok durumunu kontrol etmeliyiz

        # Tüm stok güncellemeleri yapıldıktan sonra menü öğelerinin uygunluğunu kontrol et
        for menu_item_id in menu_items_to_check_availability:
            await check_and_update_menu_item_availability(db, menu_item_id)

        await db.commit()  # Tüm değişiklikleri (order, order_items, ingredient stock, menu_item availability) tek bir işlemde commit et
        await db.refresh(order)

    # Sipariş ürünlerini getir
    item_stmt = select(OrderItem).where(OrderItem.order_id == order.id)
    item_result = await db.execute(item_stmt)
    items = item_result.scalars().all()

    name_map = {id: m.name for id, m in menu_items.items()}

    return OrderOut(
        id=order.id,
        table_id=order.table_id,
        status=order.status.value,
        items=[
            OrderItemOut(name=name_map[i.menu_item_id], quantity=i.quantity)
            for i in items
        ]
    )


# ✅ GET MY ORDERS → CUSTOMER siparişleri (DÜZELTİLDİ)
@router.get("/my-orders", response_model=list[OrderSummary], dependencies=[Depends(role_required(["CUSTOMER"]))])
async def get_my_orders(db: AsyncSession = Depends(get_async_session), user: User = Depends(get_current_user)):
    orders_result = await db.execute(select(Order).where(Order.customer_id == user.id))
    orders = orders_result.scalars().all()

    summaries = []
    for order in orders:
        item_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        order_items = item_result.scalars().all()

        item_summary = [
            OrderItemSummary(
                name=(await db.execute(select(MenuItem.name).where(MenuItem.id == i.menu_item_id))).scalar_one(),
                quantity=i.quantity
            ) for i in order_items
        ]

        summaries.append(OrderSummary(
            id=order.id,
            table_id=order.table_id,
            status=order.status.value,
            items=item_summary
        ))

    return summaries
