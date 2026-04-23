import sqlite3

import pytest

from connection.handlers import disconnect
from connection.repository import Connection, ConnectionRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = ConnectionRepository(conn)
    r.init_schema()
    return r


def test_conn_be_002_1_s1_disconnect_deletes_connection_row(repo):
    # GIVEN a known connection row exists
    repo.put(
        Connection(connection_id="conn-xyz", player_id="player-1", expires_at=9999)
    )

    # WHEN the disconnect handler runs
    disconnect(connection_id="conn-xyz", repo=repo)

    # THEN the row is removed
    assert repo.get("conn-xyz") is None


def test_conn_story_002_s1_clean_disconnect_removes_connection_record(repo):
    # GIVEN a row (connection_id, player_id) exists in the connections table
    repo.put(
        Connection(connection_id="conn-abc", player_id="player-7", expires_at=1234)
    )

    # WHEN the disconnect handler runs for that connection
    disconnect(connection_id="conn-abc", repo=repo)

    # THEN the matching row is deleted and no error is raised
    assert repo.get("conn-abc") is None


def test_conn_story_002_s2_disconnect_unknown_connection_is_noop(repo):
    # GIVEN no row for connectionId exists in the connections table
    assert repo.get("conn-unknown") is None

    # WHEN the disconnect handler runs with that connectionId
    disconnect(connection_id="conn-unknown", repo=repo)

    # THEN the handler completes without error (idempotent delete)
    assert repo.get("conn-unknown") is None
