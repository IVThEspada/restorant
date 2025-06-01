from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.table import DiningTable, TableStatus
from app.core.database import get_async_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.table import DiningTable

router = APIRouter(prefix="/customer", tags=["Customer"])

@router.post("/sit/{table_number}")
async def sit_at_table(
    table_number: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER rolü kontrolü
    if current_user.role.value != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Sadece CUSTOMER rolü masaya oturabilir.")

    # 🔸 Kullanıcı zaten bir masada mı oturuyor?
    existing_table_result = await session.execute(
        select(DiningTable).where(DiningTable.current_user_id == current_user.id)
    )
    existing_table = existing_table_result.scalar_one_or_none()

    if existing_table:
        raise HTTPException(
            status_code=400,
            detail=f"Zaten {existing_table.number} numaralı masada oturuyorsunuz."
        )

    # 🔸 Masa var mı?
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.number == table_number)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")

    # 🔸 Masa uygun mu?
    if table.status == TableStatus.OCCUPIED and table.current_user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Bu masa başka bir müşteri tarafından kullanılıyor.")

    # 🔸 Eğer zaten bu masadaysa (çok nadir durum)
    if table.current_user_id == current_user.id:
        return {"message": f"Zaten Masa {table.number} üzerinde oturuyorsunuz."}

    # 🔸 Masaya oturt
    table.status = TableStatus.OCCUPIED
    table.current_user_id = current_user.id

    await session.commit()
    await session.refresh(table)

    return {"message": f"{table.number} numaralı masaya oturdunuz."}


@router.get("/my-orders")
async def get_my_orders(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # Hangi masada oturduğunu bul
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.current_user_id == current_user.id)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        return {"table_number": None, "orders": []}

    # O masadaki siparişleri getir
    orders_result = await session.execute(
        select(Order).where(Order.table_id == table.id)
    )
    orders = orders_result.scalars().all()

    return {
        "table_number": table.number,
        "orders": [
            {"order_id": o.id, "status": o.status.value, "is_paid": o.is_paid}
            for o in orders
        ]
    }

@router.post("/leave")
async def leave_table(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # Müşterinin oturduğu masayı bul
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.current_user_id == current_user.id)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=400, detail="Şu anda herhangi bir masada değilsiniz.")

    # Sipariş kontrolü
    orders_result = await session.execute(
        select(Order).where(Order.table_id == table.id)
    )
    orders = orders_result.scalars().all()

    has_unpaid_order = any(not o.is_paid for o in orders)
    if has_unpaid_order:
        raise HTTPException(status_code=400, detail="Ödenmemiş siparişiniz olduğu için kalkamazsınız.")

    # Masayı güncelle
    table.status = TableStatus.AVAILABLE
    table.current_user_id = None

    await session.commit()
    await session.refresh(table)

    return {"message": f"{table.number} numaralı masadan kalktınız."}