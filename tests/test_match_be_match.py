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


def test_match_be_001_1_s1_second_player_triggers_match(repo):
    # GIVEN player A is waiting in the queue
    join_queue(player_id="player-A", repo=repo, now_epoch=1_700_000_000)
    assert repo.peek_waiting().player_id == "player-A"

    # WHEN player B joins
    result = join_queue(player_id="player-B", repo=repo, now_epoch=1_700_000_001)

    # THEN both players are matched and a game is created
    assert result.status == "matched"
    assert result.game is not None
    assert set(result.game["player_ids"]) == {"player-A", "player-B"}
    # initial state: 30 HP, 0 mana, active player is one of them
    for p in result.game["players"]:
        assert p["hp"] == 30
        assert p["mana"] == 0
        assert p["mana_slots"] == 0

    # AND the queue is empty
    assert repo.peek_waiting() is None

    # AND the game row is persisted
    stored = repo.get_game(result.game["game_id"])
    assert stored is not None
    assert set(stored["player_ids"]) == {"player-A", "player-B"}
