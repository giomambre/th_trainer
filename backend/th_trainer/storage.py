"""Persistenza locale di configurazioni e stato privato delle mani."""

from __future__ import annotations

import os
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def default_database_path() -> Path:
    configured = os.environ.get("TH_TRAINER_DATA_DIR")
    if configured:
        directory = Path(configured).expanduser()
    elif os.name == "nt":
        directory = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TH_trainer"
    else:
        directory = Path.home() / ".local" / "share" / "th_trainer"
    return directory / "trainer.sqlite3"


class SessionStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError(f"Versione database non supportata: {version}")
            if version == 2:
                return
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    seats INTEGER NOT NULL CHECK (seats BETWEEN 2 AND 6),
                    assistance_mode TEXT NOT NULL
                        CHECK (assistance_mode IN ('assisted', 'unassisted'))
                );
                CREATE TABLE IF NOT EXISTS hands (
                    id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL,
                    state TEXT NOT NULL
                );
                PRAGMA user_version = 2;
                COMMIT;
                """
            )

    def create(self, seats: int, assistance_mode: str) -> dict:
        session = {
            "id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seats": seats,
            "assistance_mode": assistance_mode,
        }
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO sessions (id, created_at, seats, assistance_mode)
                    VALUES (:id, :created_at, :seats, :assistance_mode)
                    """,
                    session,
                )
        return session

    def list(self) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, created_at, seats, assistance_mode
                FROM sessions
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, session_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, created_at, seats, assistance_mode
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_hand(self, state: dict) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("INSERT INTO hands (id, revision, state) VALUES (?, ?, ?)",
                               (state["id"], state["revision"], json.dumps(state)))

    def get_hand(self, hand_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT state FROM hands WHERE id = ?", (hand_id,)).fetchone()
        return json.loads(row["state"]) if row else None

    def update_hand(self, state: dict, expected_revision: int) -> bool:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "UPDATE hands SET revision = ?, state = ? WHERE id = ? AND revision = ?",
                (state["revision"], json.dumps(state), state["id"], expected_revision),
            )
            return cursor.rowcount == 1
