import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    connection_id: str
    player_id: str
    expires_at: int


class ConnectionRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
                connection_id TEXT PRIMARY KEY,
                player_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def put(self, connection: Connection) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO connections VALUES (?, ?, ?)",
            (connection.connection_id, connection.player_id, connection.expires_at),
        )
        self._conn.commit()

    def get(self, connection_id: str) -> Connection | None:
        row = self._conn.execute(
            "SELECT connection_id, player_id, expires_at FROM connections "
            "WHERE connection_id = ?",
            (connection_id,),
        ).fetchone()
        if row is None:
            return None
        return Connection(*row)
