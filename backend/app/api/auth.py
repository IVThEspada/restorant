from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.user import UserLogin
from app.schemas.user import UserCreate
from app.models.user import User, UserRole  # Rol enum'u ekle

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT ayarları
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# FastAPI security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token çözümlenemedi.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return user


@router.post("/login")
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_async_session)):
    print("📥 Gelen email:", payload.email)
    print("📥 Gelen şifre:", payload.password)

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user:
        print("✅ Veritabanı kullanıcı bulundu:", user.email)
        print("🔐 Veritabanı şifresi:", user.password)
    else:
        print("❌ Kullanıcı bulunamadı.")

    if not user or user.password != payload.password:
        print("⛔ Şifre eşleşmedi. Giriş reddedildi.")
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre.")

    print("✅ Giriş başarılı. JWT token oluşturuluyor...")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value  # 🎯 Buraya dikkat!
    }


@router.get("/debug/users")
async def list_users(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"email": u.email, "password": u.password, "role": u.role.value} for u in users]

@router.post("/register")
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_async_session)):
    # E-posta zaten kayıtlı mı?
    result = await db.execute(select(User).where(User.email == payload.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir hesap var.")

    # Yeni kullanıcı oluştur
    new_user = User(
        name=payload.name,
        email=payload.email,
        password=payload.password,  # Not: Üretim ortamında hashlenmeli
        role=UserRole.CUSTOMER  # Otomatik olarak MÜŞTERİ olarak atanır
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "Kayıt başarılı", "user_id": new_user.id}


print("✅ auth router JWT ile yüklendi ve aktif")
