from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session  # düzeltildi
from app.models.table import DiningTable
from app.schemas.table import TableCreate, TableOut, TableUpdate
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tables", tags=["tables"])

# GET /tables
@router.get("/", response_model=list[TableOut])
async def list_tables(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(DiningTable))
    return result.scalars().all()

# GET /tables/{id}
@router.get("/{table_id}", response_model=TableOut)
async def get_table(table_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(DiningTable).where(DiningTable.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")
    return table

# POST /tables
@router.post("/", response_model=TableOut, status_code=201)
async def create_table(payload: TableCreate, db: AsyncSession = Depends(get_async_session)):
    table = DiningTable(**payload.dict())
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table

# PATCH /tables/{id}
@router.patch("/{table_id}", response_model=TableOut)
async def update_table(table_id: int, payload: TableUpdate, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(DiningTable).where(DiningTable.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")

    if payload.seats is not None:
        table.seats = payload.seats
    if payload.status is not None:
        table.status = payload.status

    await db.commit()
    await db.refresh(table)
    return table

# DELETE /tables/{id}
@router.delete("/{table_id}", status_code=204)
async def delete_table(table_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(DiningTable).where(DiningTable.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")
    await db.delete(table)
    await db.commit()

@router.get("/me-test")
async def test_login(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value
    }

@router.post("/sit/{table_number}")
async def sit_at_table(
    table_number: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.number == table_number)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")

    if table.status == TableStatus.OCCUPIED and table.current_user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Bu masa başka bir müşteri tarafından kullanılıyor.")

    # Eğer zaten bu kullanıcı bu masada oturuyorsa tekrar işleme gerek yok
    if table.current_user_id == current_user.id:
        return {"message": f"Zaten Masa {table.number} üzerinde oturuyorsunuz."}

    # Masayı güncelle
    table.status = TableStatus.OCCUPIED
    table.current_user_id = current_user.id

    await session.commit()
    await session.refresh(table)

    return {"message": f"Masa {table.number} üzerinde oturdunuz."}

@router.post("/customer/leave/{table_number}")
async def leave_table(
    table_number: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    table_result = await session.execute(
        select(DiningTable).where(DiningTable.number == table_number)
    )
    table = table_result.scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı.")

    if table.current_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu masada siz oturmuyorsunuz.")

    table.status = TableStatus.AVAILABLE
    table.current_user_id = None

    await session.commit()
    await session.refresh(table)

    return {"message": f"Masa {table.number} boşaltıldı."}