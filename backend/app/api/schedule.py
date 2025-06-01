from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session  # düzeltildi
from app.schemas.schedule import ScheduleCreate, ScheduleOut
from app.models.schedule import Schedule
from app.dependencies.auth import role_required, get_current_user
from app.models.user import User

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.post("/", response_model=ScheduleOut, dependencies=[Depends(role_required(["MANAGER"]))])
async def create_schedule(
    payload: ScheduleCreate,
    db: AsyncSession = Depends(get_async_session)  # düzeltildi
):
    schedule = Schedule(**payload.dict())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.get("/", response_model=list[ScheduleOut], dependencies=[Depends(role_required(["MANAGER"]))])
async def list_all_schedules(db: AsyncSession = Depends(get_async_session)):  # düzeltildi
    result = await db.execute(select(Schedule))
    return result.scalars().all()

@router.get("/me", response_model=list[ScheduleOut])
async def get_my_schedule(
    db: AsyncSession = Depends(get_async_session),  # düzeltildi
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Schedule).where(Schedule.user_id == user.id))
    return result.scalars().all()
