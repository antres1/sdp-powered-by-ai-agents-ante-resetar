import sqlite3

import jwt
import pytest

from connection.handlers import ConnectRejectedError, connect
from connection.repository import ConnectionRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    repo = ConnectionRepository(conn)
    repo.init_schema()
    return repo


def test_conn_be_001_1_s2_invalid_jwt_rejects_without_writing(repo):
    # GIVEN a JWT signed with a wrong secret
    secret = "0123456789abcdef0123456789abcdef"  # pragma: allowlist secret
    bad_secret = "ffffffffffffffffffffffffffffffff"  # pragma: allowlist secret
    token = jwt.encode({"sub": "player-42"}, bad_secret, algorithm="HS256")

    # WHEN the connect handler runs with the server's real secret
    # THEN it raises ConnectRejectedError and does not write to the repo
    with pytest.raises(ConnectRejectedError):
        connect(
            connection_id="conn-xyz",
            token=token,
            secret=secret,
            repo=repo,
            now_epoch=1_700_000_000,
        )

    assert repo.get("conn-xyz") is None
