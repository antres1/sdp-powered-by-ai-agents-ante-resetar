import json
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class QueueEntry:
    player_id: str
    joined_at: int


class MatchmakingRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS queue (
                player_id TEXT PRIMARY KEY,
                joined_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def enqueue(self, entry: QueueEntry) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO queue VALUES (?, ?)",
            (entry.player_id, entry.joined_at),
        )
        self._conn.commit()

    def peek_waiting(self) -> QueueEntry | None:
        row = self._conn.execute(
            "SELECT player_id, joined_at FROM queue ORDER BY joined_at LIMIT 1"
        ).fetchone()
        return QueueEntry(*row) if row else None

    def pop_waiting(self) -> QueueEntry | None:
        cur = self._conn.execute(
            "SELECT player_id, joined_at FROM queue ORDER BY joined_at LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return None
        self._conn.execute("DELETE FROM queue WHERE player_id = ?", (row[0],))
        self._conn.commit()
        return QueueEntry(*row)

    def save_game(self, game_id: str, state: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO games VALUES (?, ?)",
            (game_id, json.dumps(state)),
        )
        self._conn.commit()

    def get_game(self, game_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT state_json FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def find_game_by_player(self, player_id: str) -> dict | None:
        rows = self._conn.execute("SELECT state_json FROM games").fetchall()
        for (state_json,) in rows:
            state = json.loads(state_json)
            if player_id in state.get("player_ids", []):
                return state
        return None
