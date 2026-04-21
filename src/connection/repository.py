from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConnectionRecord:
    connection_id: str
    player_id: str
    expires_at: datetime


class InMemoryConnectionRepository:
    def __init__(self) -> None:
        self._store: dict[str, ConnectionRecord] = {}

    def put(self, record: ConnectionRecord) -> None:
        self._store[record.connection_id] = record

    def get(self, connection_id: str) -> ConnectionRecord | None:
        return self._store.get(connection_id)
