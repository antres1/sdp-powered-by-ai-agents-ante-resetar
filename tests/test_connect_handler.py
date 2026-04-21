from datetime import UTC, datetime, timedelta

import jwt

from connection.handler import connect
from connection.repository import InMemoryConnectionRepository


def test_conn_be_001_1_s1_valid_jwt_stores_connection_record():
    # GIVEN a $connect event with a valid JWT containing `sub` (playerId)
    secret = "a-32-byte-test-secret-padding-xx"  # pragma: allowlist secret
    now = datetime(2026, 4, 21, 12, 0, 0, tzinfo=UTC)
    token = jwt.encode(
        {
            "sub": "player-42",
            "exp": int(datetime.now(UTC).timestamp()) + 3600,
        },
        secret,
        algorithm="HS256",
    )
    event = {
        "requestContext": {"connectionId": "conn-abc"},
        "queryStringParameters": {"token": token},
    }
    repo = InMemoryConnectionRepository()

    # WHEN ConnectFunction is invoked
    response = connect(event, repo=repo, secret=secret, now=lambda: now)

    # THEN a record PK=CONN#<connectionId> with playerId and TTL +24h is written
    stored = repo.get("conn-abc")
    assert stored is not None
    assert stored.player_id == "player-42"
    assert stored.connection_id == "conn-abc"
    assert stored.expires_at == now + timedelta(hours=24)

    # AND the function returns HTTP 200
    assert response["statusCode"] == 200
