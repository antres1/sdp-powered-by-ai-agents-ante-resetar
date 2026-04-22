import sqlite3

import jwt
import pytest

from connection.handlers import connect
from connection.repository import ConnectionRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    repo = ConnectionRepository(conn)
    repo.init_schema()
    return repo


def test_conn_be_001_1_s1_valid_jwt_stores_connection_record(repo):
    # GIVEN a connect event with a valid JWT signed with the server's secret
    secret = "0123456789abcdef0123456789abcdef"  # pragma: allowlist secret
    token = jwt.encode({"sub": "player-42"}, secret, algorithm="HS256")

    # WHEN the connect handler runs
    result = connect(
        connection_id="conn-abc",
        token=token,
        secret=secret,
        repo=repo,
        now_epoch=1_700_000_000,
    )

    # THEN the handler reports success
    assert result.accepted is True
    assert result.player_id == "player-42"

    # AND a row maps conn-abc -> player-42 with expires_at = now + 24h
    row = repo.get("conn-abc")
    assert row is not None
    assert row.player_id == "player-42"
    assert row.expires_at == 1_700_000_000 + 24 * 60 * 60
