from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from constants import DATABASE_URL

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def yield_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


def return_db() -> AsyncSession:
    session = SessionLocal()
    return session
