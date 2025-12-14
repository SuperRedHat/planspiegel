from typing import List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

from lib.postgres_db import Base
from models.message import Message


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    chat_id: int
    check_id: int
    messages: List[Message]


class ChatDB(Base):
    __tablename__ = "chats"
    chat_id: Mapped[int] = Column(Integer, primary_key=True)
    check_id: Mapped[int] = Column(Integer, ForeignKey("checks.check_id"))
    check = relationship("CheckDB", back_populates="chat", uselist=False)
    messages = relationship("MessageDB", back_populates="chat", lazy="noload")

    def to_pydantic(self) -> Chat:
        return Chat(chat_id=self.chat_id,
                    messages=[message.to_pydantic() for message in self.messages],
                    check_id=self.check_id)


async def db_save_chat(chat: ChatDB, db: AsyncSession):
    """Saves a chat object to the database.

    Args:
        chat: The ChatDB object to be saved.
        db: A database session object.

    Raises:
        Exception: If an error occurs while saving the chat.
    """
    try:
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
    except Exception as e:
        raise Exception(f"Error saving chat: {e}") from e

    return chat
