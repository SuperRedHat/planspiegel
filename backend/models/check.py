from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, JSON, ForeignKey, Enum as SqlEnum, Integer, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

from lib.postgres_db import Base
from models import Chat


class CheckType(str, Enum):
    COOKIE = "cookie"
    LIGHTHOUSE = "lighthouse"
    NETWORK = "network"
    SCAN_PORTS = "scan_ports"
    TECHNOLOGIES = "technologies"


class CheckStatus(str, Enum):
    """
    created -> running -> done || failed
    """
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Check(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    check_id: int
    check_type: CheckType
    status: CheckStatus
    results: Optional[dict] = None
    results_description: Optional[str] = None
    checkup_id: Optional[int] = None
    chat: Optional[Chat] = None


class CheckDB(Base):
    __tablename__ = "checks"
    check_id: Mapped[int] = Column(Integer, primary_key=True)
    check_type: Mapped[CheckType] = Column(SqlEnum(CheckType), nullable=False)
    status: Mapped[CheckStatus] = Column(SqlEnum(CheckStatus), nullable=False, default=CheckStatus.CREATED)
    results = Column(JSON)
    results_description: Mapped[str] = Column(String)
    checkup_id: Mapped[int] = Column(Integer, ForeignKey("checkups.checkup_id"))
    checkup = relationship("CheckupDB", back_populates="checks")
    # CheckDB 1:1 ChatDB
    chat = relationship("ChatDB", back_populates="check", uselist=False, lazy="selectin")

    def to_pydantic(self) -> Check:
        return Check.model_validate(self)


async def db_save_check(check: CheckDB, db: AsyncSession) -> Check:
    """Saves a check object to the database.

    Args:
        check: The CheckDB object to be saved.
        db: A database session object.

    Raises:
        Exception: If an error occurs while saving the check.
    """
    try:
        db.add(check)
        await db.commit()
        await db.refresh(check)
    except Exception as e:
        raise Exception(f"Error saving check: {e}") from e

    return check.to_pydantic()


async def db_complete_check_with_results(check: CheckDB, results, results_description: str, db: AsyncSession) -> Check:
    """Update a check object to the database.

    Args:
        check: The CheckDB object to be saved.
        results: check result
        results_description: short version from LLM
        db: A database session object.

    Raises:
        Exception: If an error occurs while updating the check.
    """
    try:
        check.results = results
        check.results_description = results_description
        check.status = CheckStatus.COMPLETED
        db.add(check)
        await db.commit()
        await db.refresh(check)
    except Exception as e:
        raise Exception(f"Error updating check: {e}") from e

    return check.to_pydantic()


async def db_complete_check_with_failure(check: CheckDB, failure, db: AsyncSession) -> Check:
    """Update a check object to the database.

    Args:
        check: The CheckDB object to be saved.
        failure: exception
        db: A database session object.

    Raises:
        Exception: If an error occurs while updating the check.
    """
    try:
        check.results = failure
        check.status = CheckStatus.FAILED
        db.add(check)
        await db.commit()
        await db.refresh(check)
    except Exception as e:
        raise Exception(f"Error updating check: {e}") from e

    return check.to_pydantic()


async def db_check_by_id(check_id: int, db: AsyncSession) -> Check:
    result = await db.execute(
        select(CheckDB)
        .where(CheckDB.check_id == check_id)
    )
    check_dbo = result.scalars().first()
    return check_dbo.to_pydantic()
