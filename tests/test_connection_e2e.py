from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from connection.client import ConnectionStatus, WebSocketClient
from connection.handler import connect
from connection.repository import InMemoryConnectionRepository

SECRET = "a-32-byte-test-secret-padding-xx"  # pragma: allowlist secret


def _make_token(*, expired: bool = False) -> str:
    delta = -3600 if expired else 3600
    return jwt.encode(
        {
            "sub": "player-42",
            "exp": int(datetime.now(UTC).timestamp()) + delta,
        },
        SECRET,
        algorithm="HS256",
    )


def _server_open_ws(repo: InMemoryConnectionRepository):
    """Simulate the WebSocket server that invokes the connect handler on $connect."""

    def open_ws(url: str):
        # parse token off the URL
        token = url.split("?token=", 1)[1]
        event = {
            "requestContext": {"connectionId": str(uuid4())},
            "queryStringParameters": {"token": token},
        }
        response = connect(event, repo=repo, secret=SECRET)
        if response["statusCode"] != 200:
            raise ConnectionRefusedError(f"server rejected: {response['statusCode']}")
        return object()  # opaque ws handle

    return open_ws


def test_conn_story_001_s1_valid_jwt_connects_and_record_is_written():
    # GIVEN a player with a valid JWT, and a running connection service
    repo = InMemoryConnectionRepository()
    client = WebSocketClient(
        base_url="ws://localhost:8765",
        token_provider=lambda: _make_token(),
        open_ws=_server_open_ws(repo),
    )

    # WHEN the player connects
    client.start()

    # THEN the client is CONNECTED
    assert client.status is ConnectionStatus.CONNECTED
    # AND the repository holds exactly one record for player-42
    records = [r for r in repo._store.values() if r.player_id == "player-42"]
    assert len(records) == 1
    # AND the record has a ~24h TTL
    assert records[0].expires_at > datetime.now(UTC) + timedelta(hours=23)


def test_conn_story_001_s2_invalid_jwt_is_rejected_with_no_record_written():
    # GIVEN a player holding an expired JWT
    repo = InMemoryConnectionRepository()
    client = WebSocketClient(
        base_url="ws://localhost:8765",
        token_provider=lambda: _make_token(expired=True),
        open_ws=_server_open_ws(repo),
    )

    # WHEN the player attempts to connect
    client.start()

    # THEN the client shows auth failure
    assert client.status is ConnectionStatus.AUTH_FAILED
    # AND no record is written
    assert repo._store == {}
