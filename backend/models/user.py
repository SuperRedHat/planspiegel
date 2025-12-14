from typing import Optional, List

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, select, Integer, String, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

from lib.postgres_db import Base
from models import Checkup


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: Optional[int] = None
    email: str
    hashed_password: Optional[str] = Field(default=None, exclude=True)
    is_google: bool = False
    checkups: Optional[List[Checkup]] = None


class UserDB(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String, unique=True, index=True)
    hashed_password: Mapped[str] = Column(String)
    is_google: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    checkups = relationship("CheckupDB", back_populates="owner", lazy="selectin")

    def __repr__(self):
        return f"<UserDB(id={self.user_id}, email='{self.email}', is_google='{self.is_google}')>"

    def to_pydantic(self) -> User:
        return User(
            user_id=self.user_id,
            email=self.email,
            hashed_password=self.hashed_password,
            is_google=self.is_google,
            checkups=[checkup.to_pydantic() for checkup in self.checkups])


async def db_save_user(user: User, db: AsyncSession) -> User | None:
    """
    Handles user creation/update for regular login.
    Password is REQUIRED.
    """
    if not user.hashed_password or not user.hashed_password.strip():
        raise ValueError("Password is required.")
    query = select(UserDB).where(UserDB.email == user.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if not existing_user:
        new_user = UserDB(email=user.email, hashed_password=user.hashed_password, is_google=False)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user.to_pydantic()

    elif existing_user.is_google:
        existing_user.hashed_password = user.hashed_password
        await db.commit()
        await db.refresh(existing_user)
        return existing_user.to_pydantic()

    elif not existing_user.is_google:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")


async def db_save_user_via_provider(email: str, db: AsyncSession) -> User:
    """
    provider - is one button auth like "login via Google"
    :param email: new or existing email
    :param db: DB for save
    """
    query = select(UserDB).where(UserDB.email == email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        if not existing_user.is_google:
            existing_user.is_google = True
            await db.commit()
            await db.refresh(existing_user)
        return existing_user.to_pydantic()
    else:
        new_user = UserDB(email=email, hashed_password="", is_google=True)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user.to_pydantic()


async def db_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(UserDB).where(UserDB.email == email))
    user_dbo: UserDB | None = result.scalars().first()
    if user_dbo is None:
        return None
    return user_dbo.to_pydantic()


async def db_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(UserDB).where(UserDB.user_id == user_id))
    user_dbo: UserDB | None = result.scalars().first()
    if user_dbo is None:
        return None
    return user_dbo.to_pydantic()
