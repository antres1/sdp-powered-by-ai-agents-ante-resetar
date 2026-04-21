from collections.abc import Callable
from enum import Enum
from typing import Any


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    AUTH_FAILED = "auth_failed"


class WebSocketClient:
    def __init__(
        self,
        base_url: str,
        token_provider: Callable[[], str],
        open_ws: Callable[[str], Any],
    ) -> None:
        self._base_url = base_url
        self._token_provider = token_provider
        self._open_ws = open_ws
        self._ws: Any | None = None
        self.status = ConnectionStatus.DISCONNECTED

    def start(self) -> None:
        token = self._token_provider()
        url = f"{self._base_url}?token={token}"
        self._ws = self._open_ws(url)
        self.status = ConnectionStatus.CONNECTED
