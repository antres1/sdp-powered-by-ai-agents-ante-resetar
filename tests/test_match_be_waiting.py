import sqlite3

import pytest

from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def test_match_be_001_1_s2_queue_row_written_and_waiting_response(repo):
    # GIVEN the queue table is empty
    assert repo.peek_waiting() is None

    # WHEN the join_queue handler runs for player-1
    result = join_queue(player_id="player-1", repo=repo, now_epoch=1_700_000_000)

    # THEN the player is queued and receives a waiting status
    assert result.status == "waiting"
    assert result.game is None
    row = repo.peek_waiting()
    assert row is not None
    assert row.player_id == "player-1"
    assert row.joined_at == 1_700_000_000
