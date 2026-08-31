from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.db import init_db, insert_message, list_messages


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="clippin-jimmy relay", lifespan=lifespan)


class MessageIn(BaseModel):
    sender: str = Field(min_length=1, max_length=32)
    text: str = Field(min_length=1, max_length=20000)
    type: Literal["chat", "clipboard"] = "chat"


def _validate_room(room: str) -> None:
    if not room or len(room) > 64 or "/" in room or room != room.strip():
        raise HTTPException(status_code=400, detail="invalid room")


def _validate_sender(sender: str) -> None:
    if sender != sender.strip():
        raise HTTPException(status_code=400, detail="invalid sender")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/rooms/{room}/messages")
def post_message(room: str, body: MessageIn) -> dict:
    _validate_room(room)
    _validate_sender(body.sender)
    created_at = datetime.now(timezone.utc).isoformat()
    return insert_message(room, body.sender, body.type, body.text, created_at)


@app.get("/api/rooms/{room}/messages")
def get_messages(room: str, after: int = Query(default=0, ge=0)) -> dict:
    _validate_room(room)
    return {"messages": list_messages(room, after)}
