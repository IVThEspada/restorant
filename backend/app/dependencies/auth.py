from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from typing import List
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # sadece görünüm için

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Swagger veya istemciden gelen 'Bearer user-3' ifadesinden 'user-3' ayıklanır
    if token.lower().startswith("bearer "):
        token = token[7:]  # "Bearer " kısmını keser

    if not token.startswith("user-"):
        raise HTTPException(status_code=401, detail="Geçersiz token.")

    try:
        user_id = int(token.replace("user-", ""))
    except ValueError:
        raise HTTPException(status_code=401, detail="Token formatı geçersiz.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")

    return user

def role_required(allowed_roles: List[str]):
    def dependency(user: User = Depends(get_current_user)):
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok."
            )
        return user
    return dependency
