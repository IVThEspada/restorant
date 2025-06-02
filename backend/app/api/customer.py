from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.table import DiningTable, TableStatus
from app.core.database import get_async_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus # OrderItem'ı da ekledik
from app.models.menu_item import MenuItem # MenuItem'ı da ekledik

from pydantic import BaseModel

class MessageResponse(BaseModel):
    message: str


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

    # O masadaki kullanıcının SADECE ÖDENMEMİŞ siparişlerini getir
    orders_result = await session.execute(
        select(Order)
        .where(
            Order.table_id == table.id,
            Order.customer_id == current_user.id, # Kendi siparişlerini alsın
            Order.is_paid == False # Sadece ödenmemiş siparişleri filtrele
        )
        .order_by(Order.created_at)
    )
    orders = orders_result.scalars().all()

    # Siparişler ve detaylarını hazırlama
    formatted_orders = []
    for order in orders:
        # Siparişin kalemlerini çek
        order_items_result = await session.execute(
            select(OrderItem, MenuItem.name, MenuItem.price)
            .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
            .where(OrderItem.order_id == order.id)
        )
        items = order_items_result.all()

        # Her bir OrderItem için toplam tutarı hesapla
        total_order_amount = sum((item_obj.quantity * menu_item_price) for item_obj, menu_item_name, menu_item_price in items)

        formatted_orders.append({
            "id": order.id,
            "status": order.status.value,
            "is_paid": order.is_paid,
            "total_amount": total_order_amount,
            "items": [
                {
                    "id": item_obj.id,
                    "menu_item_id": item_obj.menu_item_id,
                    "quantity": item_obj.quantity,
                    "note": item_obj.note,
                    "name": menu_item_name
                }
                for item_obj, menu_item_name, menu_item_price in items
            ]
        })

    return {
        "table_number": table.number,
        "orders": formatted_orders
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



### **Yeni Ödeme Endpoint'i: `/customer/pay-bill`**
@router.post("/pay-bill", response_model=MessageResponse)
async def pay_customer_bill(
    session: AsyncSession = Depends(get_async_session), # AsyncSession olarak güncelledik
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER rolü kontrolü
    if current_user.role.value != "CUSTOMER": # Enum değeri olduğu için .value kullandık
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece müşteriler bu işlemi yapabilir."
        )

    # Kullanıcının oturduğu masayı bul
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.current_user_id == current_user.id)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ödeme yapmak için önce bir masada olmanız gerekmektedir."
        )

    # O masadaki kullanıcının ödenmemiş siparişlerini çek
    unpaid_orders_result = await session.execute(
        select(Order).where(
            Order.table_id == table.id,
            # HATA BURADAYDI! Order.user_id yerine Order.customer_id kullanmalıyız.
            Order.customer_id == current_user.id, # DÜZELTME BURADA
            Order.is_paid == False
        )
    )
    unpaid_orders = unpaid_orders_result.scalars().all()

    if not unpaid_orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödenecek aktif bir siparişiniz bulunmamaktadır."
        )

    # Tüm ödenmemiş siparişleri ödendi olarak işaretle
    for order in unpaid_orders:
        order.is_paid = True
        session.add(order) # Değişikliği session'a ekle

    await session.commit() # Commit et
    # await session.refresh(order) # refresh tek bir obje için geçerli, for döngüsünde kullanmaya gerek yok

    return {"message": "Hesap başarıyla ödendi!"}