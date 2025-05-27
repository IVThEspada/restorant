from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.order import Order
from app.models.menu_item import MenuItem
from app.models.table import DiningTable, TableStatus
from app.schemas.order import OrderCreate, OrderOut, OrderItemOut, OrderSummary, OrderItemSummary, OrderPaymentUpdate
from app.schemas.order import OrderUpdate, OrderItemUpdate
from app.models.order import OrderStatus, OrderItem
from app.dependencies.auth import get_current_user, role_required
from app.models.user import User
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient



router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderOut)
async def place_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    # 1. Masa kontrolü
    table_result = await db.execute(select(DiningTable).where(DiningTable.id == payload.table_id))
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")

    if table.status in [TableStatus.CLOSED, TableStatus.RESERVED]:
        raise HTTPException(status_code=400, detail=f"Masa şu anda uygun değil. (Durum: {table.status.value})")

    # 2. Menüden sipariş verilen ürünleri çek
    menu_stmt = select(MenuItem).where(MenuItem.id.in_([i.menu_item_id for i in payload.items]))
    result = await db.execute(menu_stmt)
    menu_items = {m.id: m for m in result.scalars().all()}

    # 3. Ürün geçerliliği ve stok kontrolü
    for item in payload.items:
        mi = menu_items.get(item.menu_item_id)
        if not mi:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: id={item.menu_item_id}")
        if not mi.is_available:
            raise HTTPException(status_code=400, detail=f"'{mi.name}' ürünü şu anda siparişe kapalı.")

    # 4. Siparişi kaydet
    order = Order(table_id=payload.table_id)
    db.add(order)
    await db.flush()  # ID oluşturulsun

    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
            note=item.note
        ))
    # 5. Stokları azalt
    for item in payload.items:
        # Menü öğesine bağlı malzemeleri çek
        ingredient_result = await db.execute(
            select(MenuItemIngredient).where(MenuItemIngredient.menu_item_id == item.menu_item_id)
        )
        used_ingredients = ingredient_result.scalars().all()

        for usage in used_ingredients:
            # İlgili malzemeyi getir
            ingredient_result = await db.execute(
                select(Ingredient).where(Ingredient.id == usage.ingredient_id)
            )
            ingredient = ingredient_result.scalar_one_or_none()

            if ingredient:
                # Sipariş adedi × kullanılan miktar kadar azalt
                ingredient.stock_quantity -= usage.amount_used * item.quantity

    await db.commit()
    await db.refresh(order)

    # 5. OrderItem + ürün adlarını çek
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


@router.patch("/{order_id}", dependencies=[Depends(role_required(["CUSTOMER"]))])
async def update_order(
        order_id: int,
        payload: OrderUpdate,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    # Siparişi bul
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if order.status != OrderStatus.RECEIVED:
        raise HTTPException(status_code=400, detail="Sipariş güncellenemez (hazırlanıyor ya da hazır).")

    # Mevcut order_items'ı sil
    await db.execute(select(OrderItem).where(OrderItem.order_id == order.id).delete())

    # Yeni order_items ekle
    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
            note=item.note
        ))

    await db.commit()
    await db.refresh(order)

    return {"message": "Sipariş başarıyla güncellendi."}

@router.patch("/{order_id}/status")
async def advance_order_status(
    order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    next_status = {
        OrderStatus.RECEIVED: OrderStatus.PREPARING,
        OrderStatus.PREPARING: OrderStatus.READY,
        OrderStatus.READY: OrderStatus.PAID
    }.get(order.status)

    if not next_status:
        raise HTTPException(status_code=400, detail="Bu siparişin statüsü daha fazla değiştirilemez.")

    order.status = next_status
    await db.commit()
    await db.refresh(order)

    return {
        "id": order.id,
        "status": order.status.value
    }

@router.delete("/{order_id}", dependencies=[Depends(role_required(["CUSTOMER", "MANAGER"]))])
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    # CUSTOMER sadece RECEIVED siparişi silebilir
    if user.role.value == "CUSTOMER" and order.status != OrderStatus.RECEIVED:
        raise HTTPException(status_code=403, detail="Bu siparişi iptal edemezsiniz.")

    # order_items sil
    await db.execute(select(OrderItem).where(OrderItem.order_id == order.id).delete())

    await db.delete(order)
    await db.commit()

    return {"message": f"Sipariş #{order.id} iptal edildi."}




@router.get("/", response_model=list[OrderSummary], dependencies=[Depends(role_required(["MANAGER"]))])
async def list_all_orders(
    db: AsyncSession = Depends(get_db)
):
    orders_result = await db.execute(select(Order))
    orders = orders_result.scalars().all()

    summaries = []
    for order in orders:
        item_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        order_items = item_result.scalars().all()

        item_summary = [
            OrderItemSummary(
                name=(await db.execute(select(MenuItem.name).where(MenuItem.id == i.menu_item_id))).scalar_one(),
                quantity=i.quantity
            )
            for i in order_items
        ]

        summaries.append(OrderSummary(
            id=order.id,
            table_id=order.table_id,
            status=order.status.value,
            items=item_summary
        ))

    return summaries


@router.patch("/{order_id}/pay", dependencies=[Depends(role_required(["WAITER", "MANAGER"]))])
async def mark_order_paid(
        order_id: int,
        payment: OrderPaymentUpdate,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if order.is_paid:
        raise HTTPException(status_code=400, detail="Sipariş zaten ödenmiş.")

    order.payment_method = payment.payment_method
    order.is_paid = True
    order.processed_by_id = user.id  # ödeme kaydını yapan kişi

    await db.commit()
    return {"message": f"Sipariş #{order.id} için ödeme kaydedildi ({payment.payment_method})."}


@router.post("/{order_id}/pay-online", dependencies=[Depends(role_required(["CUSTOMER"]))])
async def pay_order_online(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if order.is_paid:
        raise HTTPException(status_code=400, detail="Sipariş zaten ödenmiş.")

    order.payment_method = "online"
    order.is_paid = True
    order.processed_by_id = None  # sistem işliyor

    await db.commit()

    return {"message": f"Sipariş #{order.id} online ödeme ile tamamlandı."}


