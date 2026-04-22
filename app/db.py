"""db.py - Database setup + tables. That's it."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from sqlmodel import Field, SQLModel, Session, Relationship, create_engine
from sqlalchemy import URL


# --- Tables --- 
class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = "New chat"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: list["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str       # "user" or "assistant"
    content: str
    conversation: Conversation | None = Relationship(back_populates="messages")


# --- Engine + Session ---

# engine = create_engine("sqlite:///chats.db", connect_args={"check_same_thread": False})

url_object = URL.create(
    "postgresql+psycopg",
    username="postgres",
    password="1234",  # plain (unescaped) text
    host="localhost",
    database="Agentic_Hello_API",
)

engine = create_engine(url_object)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
