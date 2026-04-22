"""Inference API for the Hello AI Agent.

Run:
    Development:  fastapi dev
    Production:   fastapi run
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .agent_setup import run_agent
from .db import Conversation, Message, SessionDep, init_db
from .schemas import ChatIn, ChatOut, ConversationOut
from .config import get_settings


settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    description="A beginner-friendly inference API that wraps an AI agent.",
    version=settings.version,
    lifespan=lifespan,
)


@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "agent": "Hello AI Agent", "version": settings.version}


@app.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED, tags=["conversations"])
def create_conversation(session: SessionDep):
    """Create a new conversation."""
    convo = Conversation()
    session.add(convo)
    session.commit()
    session.refresh(convo)
    return convo


@app.post("/conversations/{cid}/chat", response_model=ChatOut, tags=["conversations"])
async def chat(cid: int, body: ChatIn, session: SessionDep):
    """Send a message, get the agent's reply, and persist both."""
    convo = session.get(Conversation, cid)
    if not convo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    history = [{"role": m.role, "content": m.content} for m in convo.messages]

    try:
        reply = await run_agent(history, body.message)
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Agent execution failed")

    session.add(Message(conversation_id=cid, role="user", content=body.message))
    session.add(Message(conversation_id=cid, role="assistant", content=reply))

    # if convo.title == "New chat":
    #     convo.title = body.message[:50]
    #     session.add(convo)

    session.commit()
    return ChatOut(reply=reply, conversation_id=cid)
