"""API locale e distribuzione del frontend compilato."""

from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .storage import SessionStore, default_database_path
from .game import Hand
from .bots import advance_test_bot


class SessionCreate(BaseModel):
    seats: int = Field(ge=2, le=6)
    assistance_mode: Literal["assisted", "unassisted"]


class SessionRead(SessionCreate):
    id: str
    created_at: str


class HandCreate(BaseModel):
    dealer: Literal[0, 1] = 0


class HandAction(BaseModel):
    action: Literal["fold", "check", "call", "raise"]
    raise_to: int | None = Field(default=None, strict=True, ge=0)
    revision: int = Field(ge=0, strict=True)


def create_app(database_path: Path | None = None) -> FastAPI:
    store = SessionStore(database_path or default_database_path())

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        store.initialize()
        yield

    app = FastAPI(title="TH Trainer", version="0.1.0", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/sessions", response_model=list[SessionRead])
    def list_sessions() -> list[dict]:
        return store.list()

    @app.post("/api/sessions", response_model=SessionRead, status_code=201)
    def create_session(request: SessionCreate) -> dict:
        return store.create(request.seats, request.assistance_mode)

    @app.get("/api/sessions/{session_id}", response_model=SessionRead)
    def get_session(session_id: str) -> dict:
        session = store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Sessione non trovata")
        return session

    def load_hand(hand_id: str) -> Hand:
        state = store.get_hand(hand_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Mano non trovata")
        return Hand(state)

    @app.post("/api/hands", status_code=201)
    def create_hand(request: HandCreate) -> dict:
        hand = Hand.new(request.dealer)
        hand.playback.append({"kind": "setup", "hand": deepcopy(hand.view())})
        advance_test_bot(hand)
        store.create_hand(hand.state)
        return hand.response()

    @app.get("/api/hands/{hand_id}")
    def get_hand(hand_id: str) -> dict:
        return load_hand(hand_id).view()

    @app.post("/api/hands/{hand_id}/actions")
    def act(hand_id: str, request: HandAction) -> dict:
        hand = load_hand(hand_id)
        if hand.state["revision"] != request.revision:
            raise HTTPException(status_code=409, detail="La mano è cambiata. Stato aggiornato: ripeti la scelta.")
        try:
            hand.act(0, request.action, request.raise_to)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        advance_test_bot(hand)
        hand.state["revision"] += 1
        if not store.update_hand(hand.state, request.revision):
            raise HTTPException(status_code=409, detail="La mano è cambiata. Stato aggiornato: ripeti la scelta.")
        return hand.response()

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if (frontend_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app


app = create_app()
