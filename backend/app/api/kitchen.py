from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.menu_item import MenuItem
from app.schemas.order import OrderOut, OrderItemOut

router = APIRouter(prefix="/kitchen", tags=["kitchen"])

@router.get("/queue", response_model=list[OrderOut])
async def get_kitchen_queue(db: AsyncSession = Depends(get_db)):
    # 1. RECEIVED durumundaki siparişleri getir
    order_stmt = select(Order).where(Order.status == OrderStatus.RECEIVED)
    orders_result = await db.execute(order_stmt)
    orders = orders_result.scalars().all()

    # 2. Sipariş ID'lerini topla
    order_ids = [o.id for o in orders]

    # 3. Tüm OrderItem'ları tek seferde çek
    item_stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    item_result = await db.execute(item_stmt)
    all_items = item_result.scalars().all()

    # 4. Menü isimlerini getir
    menu_result = await db.execute(select(MenuItem.id, MenuItem.name))
    menu_map = {id: name for id, name in menu_result.all()}

    # 5. Siparişleri birleştir
    order_map = {order.id: order for order in orders}
    for item in all_items:
        if not hasattr(order_map[item.order_id], 'item_list'):
            order_map[item.order_id].item_list = []
        order_map[item.order_id].item_list.append(item)

    # 6. JSON olarak dön
    response = []
    for order in orders:
        response.append(OrderOut(
            id=order.id,
            table_id=order.table_id,
            status=order.status.value,
            items=[
                OrderItemOut(name=menu_map[i.menu_item_id], quantity=i.quantity)
                for i in getattr(order, 'item_list', [])
            ]
        ))

    return response
