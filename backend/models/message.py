from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SqlEnum, func, Integer, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

from lib.postgres_db import Base


class SenderType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_id: int
    created_at: Optional[datetime] = None
    content: str
    attachment_url: Optional[str] = None
    sender_type: SenderType = SenderType.USER
    chat_id: int

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, created_at={self.created_at}, content='{self.content[:20] if self.content else ''}...', sender_type='{self.sender_type}', attachment_url='{self.attachment_url}...', chat_id={self.chat_id})>"


class MessageDB(Base):
    __tablename__ = "messages"
    message_id: Mapped[int] = Column(Integer, primary_key=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content: Mapped[str] = Column(String, nullable=False)

    attachment_url: Mapped[str] = Column(String)
    sender_type: Mapped[SenderType] = Column(SqlEnum(SenderType), nullable=False, default=SenderType.USER)

    chat_id: Mapped[int] = Column(Integer, ForeignKey("chats.chat_id"))
    chat = relationship("ChatDB", back_populates="messages")

    def __repr__(self):
        return f"<MessageDB(message_id={self.message_id}, created_at={self.created_at}, content='{self.content[:20] if self.content else ''}...', sender_type='{self.sender_type}', attachment_url='{self.attachment_url}...', chat_id={self.chat_id})>"

    def to_pydantic(self) -> Message:
        return Message.model_validate(self)


async def db_save_message(message: MessageDB, db: AsyncSession):
    """Saves a message object to the database.

    Args:
        message: The MessageDB object to be saved.
        db: A database session object.

    Raises:
        Exception: If an error occurs while saving the message.
    """
    try:
        db.add(message)
        await db.commit()
        await db.refresh(message)
    except Exception as e:
        raise Exception(f"Error saving message: {e}") from e

    return message.to_pydantic()


async def db_append_message_content(message: MessageDB, content_part: str, db: AsyncSession):
    """Saves a message object to the database.

    Args:
        message: The MessageDB object to be saved.
        content_part: part of answer from AI
        db: A database session object.

    Raises:
        Exception: If an error occurs while saving the message.
    """
    try:
        message.content += content_part
        db.add(message)
        await db.commit()
        await db.refresh(message)
    except Exception as e:
        raise Exception(f"Error updating message: {e}") from e

    return message.to_pydantic()


async def db_messages_by_chat_id(chat_id: int, db: AsyncSession) -> List[Message]:
    """Retrieves messages by chat_id.

    Args:
        chat_id: chat id
        db: A database session object.
    """
    result = await db.execute(
        select(MessageDB)
        .where(MessageDB.chat_id == chat_id)
        .order_by(MessageDB.created_at.desc())
    )
    message_dbos = result.scalars().all()
    return [message.to_pydantic() for message in message_dbos]


async def db_delete_messages_by_chat_id(chat_id: int, db: AsyncSession):
    """Delete checkup objects for the user.

    Args:
        chat_id: chat id
        db: A database session object.
    """
    stmt = delete(MessageDB).where(MessageDB.chat_id == chat_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
