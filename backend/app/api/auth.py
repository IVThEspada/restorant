from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre.")

    return {
        "access_token": f"user-{user.id}",
        "token_type": "bearer"
    }
print("✅ auth router yüklendi")