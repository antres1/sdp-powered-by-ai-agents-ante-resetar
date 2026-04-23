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


def test_match_story_002_s1_player_receives_waiting_when_queue_is_empty(repo):
    # GIVEN the queue is empty
    # WHEN a connected player joins
    result = join_queue(player_id="player-1", repo=repo, now_epoch=1_700_000_000)

    # THEN queue row written, waiting status returned, no game created
    assert result.status == "waiting"
    assert result.game is None
    assert repo.peek_waiting().player_id == "player-1"


def test_match_story_002_s2_queue_insert_is_idempotent_no_duplicate_row(repo):
    # GIVEN a row for this player already exists in the queue
    from matchmaking.repository import QueueEntry

    repo.enqueue(QueueEntry(player_id="player-1", joined_at=1_700_000_000))

    # WHEN the same player enqueues again (INSERT OR IGNORE)
    repo.enqueue(QueueEntry(player_id="player-1", joined_at=1_700_000_001))

    # THEN only one queue entry exists — no duplicate row written
    count = repo._conn.execute(
        "SELECT COUNT(*) FROM queue WHERE player_id = 'player-1'"
    ).fetchone()[0]
    assert count == 1
