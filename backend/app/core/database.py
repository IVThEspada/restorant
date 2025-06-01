from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost:5432/restaurant"

# Engine ve Session factory
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Base class
class Base(DeclarativeBase):
    pass

# Session generator (!!! dikkat: contextmanager değil !!!)
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
