import sqlite3

import pytest

from game.handlers import PlayCardResult, play_card_handler
from matchmaking.repository import MatchmakingRepository


def _initial_game(game_id: str) -> dict:
    return {
        "game_id": game_id,
        "player_ids": ["p1", "p2"],
        "active_player_index": 0,
        "players": [
            {
                "id": "p1",
                "hp": 30,
                "mana": 4,
                "mana_slots": 4,
                "hand": [1, 3, 2],
                "deck": [],
            },
            {"id": "p2", "hp": 30, "mana": 0, "mana_slots": 0, "hand": [], "deck": []},
        ],
    }


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    r.save_game("g1", _initial_game("g1"))
    return r


def test_game_be_001_1_s1_valid_play_persists_and_returns_updated_state(repo):
    # GIVEN saved game: p1 active, mana=4, can play card index 1 (cost=3)
    # WHEN the handler runs for p1
    result = play_card_handler(
        game_id="g1", acting_player_id="p1", card_index=1, repo=repo
    )

    # THEN it returns the updated state and the repo now holds the new state
    assert isinstance(result, PlayCardResult)
    assert result.error is None
    assert result.game is not None
    # active player's mana reduced 4->1; card removed; opponent HP 30->27
    assert result.game["players"][0]["mana"] == 1
    assert result.game["players"][0]["hand"] == [1, 2]
    assert result.game["players"][1]["hp"] == 27
    stored = repo.get_game("g1")
    assert stored["players"][1]["hp"] == 27


def test_game_be_001_1_s2_insufficient_mana_returns_error_and_does_not_persist(repo):
    # GIVEN a saved game where p1 will try to play a card that costs too much
    # override state so mana=2 and card index 0 costs 5 forcing the error
    repo.save_game(
        "g1",
        {
            **_initial_game("g1"),
            "players": [
                {
                    "id": "p1",
                    "hp": 30,
                    "mana": 2,
                    "mana_slots": 2,
                    "hand": [5, 3],
                    "deck": [],
                },
                {
                    "id": "p2",
                    "hp": 30,
                    "mana": 0,
                    "mana_slots": 0,
                    "hand": [],
                    "deck": [],
                },
            ],
        },
    )

    # WHEN p1 tries to play card 0 (cost=5, mana=2)
    result = play_card_handler(
        game_id="g1", acting_player_id="p1", card_index=0, repo=repo
    )

    # THEN an error is returned and state is unchanged
    assert result.error == "not enough mana"
    assert result.game is None
    stored = repo.get_game("g1")
    assert stored["players"][0]["mana"] == 2  # unchanged
    assert stored["players"][0]["hand"] == [5, 3]


def test_game_be_001_1_s3_not_active_player_returns_error(repo):
    # WHEN the inactive player (p2) tries to play
    result = play_card_handler(
        game_id="g1", acting_player_id="p2", card_index=0, repo=repo
    )

    # THEN error is "not your turn" and state is unchanged
    assert result.error == "not your turn"
    assert result.game is None
    stored = repo.get_game("g1")
    assert stored["players"][0]["mana"] == 4
