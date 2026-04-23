import sqlite3

import pytest

from game.handlers import rejoin
from matchmaking.repository import MatchmakingRepository


def _saved_game() -> dict:
    return {
        "game_id": "g1",
        "player_ids": ["p1", "p2"],
        "active_player_index": 0,
        "players": [
            {"id": "p1", "hp": 30, "mana": 3, "mana_slots": 3, "hand": [1], "deck": []},
            {"id": "p2", "hp": 28, "mana": 0, "mana_slots": 2, "hand": [], "deck": [4]},
        ],
    }


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    r.save_game("g1", _saved_game())
    return r


def test_game_be_007_1_s1_active_game_found_returns_rejoined(repo):
    # GIVEN the connectionId maps to a player with an active game
    # WHEN the rejoin handler is invoked
    result = rejoin(player_id="p1", game_repo=repo)
    # THEN status is "rejoined" and game state is returned
    assert result["status"] == "rejoined"
    assert result["game"]["game_id"] == "g1"
    assert result["game"]["players"][0]["id"] == "p1"


def test_game_be_007_1_s2_no_active_game_returns_no_active_game(repo):
    # GIVEN no game exists for this player
    # WHEN the rejoin handler is invoked
    result = rejoin(player_id="unknown_player", game_repo=repo)
    # THEN status is "no_active_game"
    assert result["status"] == "no_active_game"
