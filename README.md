# Agentic Hello API

A beginner-friendly FastAPI inference service that wraps an AI agent (OpenAI Agents SDK) backed by a local Ollama model, with persistent multi-turn conversations stored via SQLModel.

## Features

- **FastAPI** app with auto-generated OpenAPI docs at `/docs`.
- **OpenAI Agents SDK** agent (`Hello Agent`) with a `greet` function-tool.
- **Ollama provider** plugged into the Agents SDK via `OpenAIChatCompletionsModel` — run LLMs locally, no cloud key needed.
- **Persistent conversations** using SQLModel (SQLite by default, Postgres supported).
- **Pydantic-Settings** configuration loaded from `.env`.
- **Lifespan-managed DB init** (tables auto-created on startup).

## Project Structure

```
agentic-hello-api/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, lifespan, endpoints
│   ├── agent_setup.py     # Agent + greet tool + run_agent helper
│   ├── config.py          # Settings (pydantic-settings)
│   ├── db.py              # SQLModel engine, Conversation/Message tables, session dep
│   └── schemas.py         # ChatIn / ChatOut / ConversationOut
├── shared/
│   └── models/
│       ├── ollama_provider.py   # get_model() -> OpenAIChatCompletionsModel
│       └── hf_provider.py       # (placeholder for HuggingFace)
├── .env.example
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Prerequisites

- Python `>= 3.11.14`
- [uv](https://docs.astral.sh/uv/) for dependency management
- [Ollama](https://ollama.com/) running locally with a tool-calling model pulled

```bash
ollama pull qwen2.5:7b   # or llama3.1, mistral, qwen3
```

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# edit .env as needed
```

### Environment variables (`.env`)

| Variable          | Default                          | Description                                   |
|-------------------|----------------------------------|-----------------------------------------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1`      | Ollama OpenAI-compatible endpoint             |
| `OLLAMA_MODEL`    | `qwen2.5:7b`                     | Ollama model name (must support tool calling) |
| `DATABASE_URL`    | `sqlite:///./chats.db`           | SQLAlchemy URL; Postgres also supported       |
| `CORS_ORIGINS`    | `*`                              | Allowed CORS origins                          |
| `LOG_LEVEL`       | `INFO`                           | Log level                                     |

Postgres example:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/test_db
```

## Running the Server

```bash
# Development (auto-reload, 127.0.0.1)
fastapi dev app/main.py

# Production (no reload, 0.0.0.0)
fastapi run app/main.py
```

Swagger UI: **http://localhost:8000/docs**

## API Endpoints

| Method | Path                          | Description                                              |
|--------|-------------------------------|----------------------------------------------------------|
| GET    | `/`                           | Health check — returns status, agent name, version       |
| POST   | `/conversations`              | Create a new conversation, returns `{id, title, created_at}` |
| POST   | `/conversations/{cid}/chat`   | Send a message to a conversation; persists user + assistant turns and returns the reply |

### Example flow

```bash
# 1. Create a conversation
curl -X POST http://localhost:8000/conversations
# -> {"id": 1, "title": "New chat", "created_at": "..."}

# 2. Chat in that conversation
curl -X POST http://localhost:8000/conversations/1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi! My name is Ahmad."}'
# -> {"reply": "Hello, Ahmad! Welcome to Agentic AI Hub!", "conversation_id": 1}

# 3. Continue — history is loaded from DB automatically
curl -X POST http://localhost:8000/conversations/1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I just tell you?"}'
```

### Python client

```python
import requests

base = "http://localhost:8000"
cid = requests.post(f"{base}/conversations").json()["id"]

r = requests.post(
    f"{base}/conversations/{cid}/chat",
    json={"message": "Hi! My name is Ahmad."},
)
print(r.json())
```

## How It Works

1. **`main.py`** wires up FastAPI. On startup, `lifespan` calls `init_db()` which creates the `conversation` and `message` tables.
2. **`POST /conversations/{cid}/chat`** loads existing `Message` history from the DB, hands it (plus the new user message) to `run_agent`, then persists both the user message and assistant reply.
3. **`agent_setup.py`** defines a single `Agent` with a `greet` function-tool and runs it through `Runner.run(...)` from the OpenAI Agents SDK.
4. **`shared/models/ollama_provider.py`** builds an `OpenAIChatCompletionsModel` pointed at the local Ollama server, so the Agents SDK talks to Ollama as if it were OpenAI.

## Data Model

- `Conversation(id, title, created_at, messages)`
- `Message(id, conversation_id, role, content, created_at)`

SQLite DB file (`chats.db`) is created in the project root on first run.

## Tech Stack

- FastAPI (+ Uvicorn) — `fastapi[standard]`
- OpenAI Agents SDK — `openai-agents`
- SQLModel + SQLAlchemy (SQLite / Postgres via `psycopg[binary]`)
- Pydantic / pydantic-settings
- Ollama (local LLM runtime)

## What's Next

1. Add a `GET /conversations/{cid}` endpoint to fetch full history.
2. Auto-title a conversation from its first user message.
3. Stream responses via Server-Sent Events.
4. Add API-key authentication and rate limiting.
5. Wire in the `CORSMiddleware` (currently imported but not yet registered).
6. Apply guardrails — input, output, and tool.
