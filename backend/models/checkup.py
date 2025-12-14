from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, ForeignKey, Integer, select, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped, joinedload

from lib.postgres_db import Base
from models import Check


class Checkup(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: str
    checkup_id: Optional[int] = None
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None
    checks: Optional[List[Check]] = None


class CheckupDB(Base):
    __tablename__ = "checkups"
    checkup_id: Mapped[int] = Column(Integer, primary_key=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now(), nullable=False)
    url: Mapped[str] = Column(String)
    owner_id: Mapped[int] = Column(Integer, ForeignKey("users.user_id"))
    owner = relationship("UserDB", back_populates="checkups")
    checks = relationship("CheckDB", back_populates="checkup", lazy="noload")

    def to_pydantic(self) -> Checkup:
        return Checkup(
            url=self.url,
            checkup_id=self.checkup_id,
            owner_id=self.owner_id,
            created_at=self.created_at,
            checks=[check.to_pydantic() for check in self.checks] if self.checks else None,
        )


async def db_save_checkup(checkup: CheckupDB, db: AsyncSession) -> Checkup:
    """Saves a checkup object to the database.

    Args:
        checkup: The CheckupDB object to be saved.
        db: A database session object.

    Raises:
        Exception: If an error occurs while saving the checkup.
    """
    try:
        db.add(checkup)
        await db.commit()
        await db.refresh(checkup)
    except Exception as e:
        raise Exception(f"Error saving checkup: {e}") from e

    return checkup.to_pydantic()


async def db_checkups_by_user_id(user_id: int, db: AsyncSession) -> List[Checkup]:
    """Retrieves checkup objects for the user.

    Args:
        user_id: user that checkups belong
        db: A database session object.
    """
    result = await db.execute(
        select(CheckupDB)
        .where(CheckupDB.owner_id == user_id)
        .order_by(CheckupDB.created_at.desc())
    )
    checkup_dbos = result.scalars().all()
    return [checkup.to_pydantic() for checkup in checkup_dbos]


async def db_checkup_by_id(checkup_id: int, db: AsyncSession) -> Checkup | None:
    """Retrieves checkup objects for the user.

    Args:
        checkup_id: user that checkups belong
        db: A database session object.
    """
    result = await db.execute(
        select(CheckupDB)
        .where(CheckupDB.checkup_id == checkup_id)
        .options(joinedload(CheckupDB.checks)))
    checkup_dbo = result.scalars().first()
    if checkup_dbo is None:
        return None

    return checkup_dbo.to_pydantic()
