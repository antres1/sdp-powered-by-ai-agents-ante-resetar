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


def test_match_story_001_s1_two_players_match_successfully(repo):
    # GIVEN player A is waiting
    a = join_queue(player_id="player-A", repo=repo, now_epoch=1_700_000_000)
    assert a.status == "waiting"

    # WHEN player B joins
    b = join_queue(player_id="player-B", repo=repo, now_epoch=1_700_000_001)

    # THEN both are matched, queue is empty, a game exists
    assert b.status == "matched"
    assert repo.peek_waiting() is None
    assert repo.get_game(b.game["game_id"]) is not None


def test_match_story_001_s2_first_player_to_join_receives_waiting(repo):
    # GIVEN the queue is empty
    # WHEN a connected player joins
    result = join_queue(player_id="player-1", repo=repo, now_epoch=1_700_000_000)

    # THEN the player is queued and receives waiting status
    assert result.status == "waiting"
    assert result.game is None
    assert repo.peek_waiting().player_id == "player-1"
