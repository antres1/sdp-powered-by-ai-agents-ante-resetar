import sqlite3

import pytest

from game.handlers import end_turn_handler
from matchmaking.repository import MatchmakingRepository


def _saved_game() -> dict:
    return {
        "game_id": "g1",
        "player_ids": ["p1", "p2"],
        "active_player_index": 0,
        "players": [
            {
                "id": "p1",
                "hp": 30,
                "mana": 3,
                "mana_slots": 3,
                "hand": [1],
                "deck": [],
            },
            {
                "id": "p2",
                "hp": 30,
                "mana": 0,
                "mana_slots": 3,
                "hand": [],
                "deck": [4, 5],
            },
        ],
    }


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    r.save_game("g1", _saved_game())
    return r


def test_game_be_002_1_s1_end_turn_applied_and_persisted(repo):
    result = end_turn_handler(game_id="g1", acting_player_id="p1", repo=repo)
    assert result.error is None
    assert result.game["active_player_index"] == 1
    assert result.game["players"][1]["mana_slots"] == 4
    assert result.game["players"][1]["hand"] == [4]
    stored = repo.get_game("g1")
    assert stored["active_player_index"] == 1


def test_game_be_002_1_s2_wrong_player_rejected(repo):
    result = end_turn_handler(game_id="g1", acting_player_id="p2", repo=repo)
    assert result.error == "not your turn"
    assert repo.get_game("g1")["active_player_index"] == 0
