import sqlite3

import jwt
import pytest

from connection.handlers import ConnectRejectedError, connect
from connection.repository import ConnectionRepository

SECRET = "0123456789abcdef0123456789abcdef"  # pragma: allowlist secret


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    repo = ConnectionRepository(conn)
    repo.init_schema()
    return repo


def test_conn_story_001_s1_successful_connect_records_mapping(repo):
    # GIVEN a valid JWT signed with the server's secret
    token = jwt.encode({"sub": "player-1"}, SECRET, algorithm="HS256")

    # WHEN the player connects
    result = connect(
        connection_id="conn-1",
        token=token,
        secret=SECRET,
        repo=repo,
        now_epoch=1_700_000_000,
    )

    # THEN the connection is accepted and recorded
    assert result.accepted is True
    row = repo.get("conn-1")
    assert row is not None
    assert row.player_id == "player-1"


def test_conn_story_001_s2_connect_rejected_with_invalid_jwt(repo):
    # GIVEN a JWT signed with the wrong secret (stand-in for an expired/forged token)
    token = jwt.encode(
        {"sub": "player-2"},
        "ffffffffffffffffffffffffffffffff",  # pragma: allowlist secret
        algorithm="HS256",
    )

    # WHEN the player attempts to connect
    # THEN it is rejected and nothing is recorded
    with pytest.raises(ConnectRejectedError):
        connect(
            connection_id="conn-2",
            token=token,
            secret=SECRET,
            repo=repo,
            now_epoch=1_700_000_000,
        )
    assert repo.get("conn-2") is None
