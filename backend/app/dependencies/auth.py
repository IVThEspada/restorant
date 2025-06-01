from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_async_session
from app.models.user import User

from jose import JWTError, jwt

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

# 🚀 Eksik olan buydu! Ekle:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token çözümlenemedi.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")

    return user


# Rol kontrolü için bağımlılık
def role_required(allowed_roles: List[str]):
    def dependency(user: User = Depends(get_current_user)):
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok."
            )
        return user
    return dependency

# Aktif kullanıcı kontrolü (örneğin hesabı pasifse engellemek için kullanabilirsin)
async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    # Eğer kullanıcı durum kontrolü eklenecekse buraya yazılır
    return user
