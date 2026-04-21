from connection.client import ConnectionStatus, WebSocketClient


class FakeWebSocket:
    def __init__(self, url: str):
        self.url = url
        self.opened = True

    def close(self) -> None:
        self.opened = False


def test_conn_fe_001_1_s1_client_opens_connection_with_token_on_start():
    # GIVEN the player is logged in and holds a valid JWT
    jwt_token = "valid.jwt.token"  # pragma: allowlist secret
    opened_urls: list[str] = []

    def open_ws(url: str) -> FakeWebSocket:
        opened_urls.append(url)
        return FakeWebSocket(url)

    client = WebSocketClient(
        base_url="ws://localhost:8765",
        token_provider=lambda: jwt_token,
        open_ws=open_ws,
    )

    # WHEN the page initialises (client.start)
    client.start()

    # THEN the client opens a WebSocket with ?token=<JWT>
    assert opened_urls == ["ws://localhost:8765?token=valid.jwt.token"]
    # AND the connection status is "Connected"
    assert client.status is ConnectionStatus.CONNECTED


def test_conn_fe_001_1_s2_client_shows_auth_error_and_does_not_reconnect():
    # GIVEN the stored JWT is expired (the server rejects the connection)
    jwt_token = "expired.jwt.token"  # pragma: allowlist secret
    open_attempts: list[str] = []

    def failing_open_ws(url: str):
        open_attempts.append(url)
        raise ConnectionRefusedError("401 Unauthorized")

    client = WebSocketClient(
        base_url="ws://localhost:8765",
        token_provider=lambda: jwt_token,
        open_ws=failing_open_ws,
    )

    # WHEN the client attempts to connect
    client.start()

    # THEN the status moves to AUTH_FAILED
    assert client.status is ConnectionStatus.AUTH_FAILED
    # AND the UI message reflects the failure
    assert client.error_message == "Authentication failed — please log in again"
    # AND no automatic reconnect is attempted
    assert len(open_attempts) == 1
