import sqlite3

import pytest

from game.handlers import end_turn_handler, play_card_handler
from matchmaking.repository import MatchmakingRepository


def _game(hp_opp=30, mana=10, hand=None, opp_deck=None):
    return {
        "game_id": "g1",
        "player_ids": ["p1", "p2"],
        "active_player_index": 0,
        "players": [
            {
                "id": "p1",
                "hp": 30,
                "mana": mana,
                "mana_slots": mana,
                "hand": list(hand or [5]),
                "deck": [],
            },
            {
                "id": "p2",
                "hp": hp_opp,
                "mana": 0,
                "mana_slots": 0,
                "hand": [],
                "deck": list(opp_deck or []),
            },
        ],
    }


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def test_game_be_003_2_s1_play_card_emits_winner_on_lethal_damage(repo):
    repo.save_game("g1", _game(hp_opp=2, mana=3, hand=[3]))
    result = play_card_handler(
        game_id="g1", acting_player_id="p1", card_index=0, repo=repo
    )
    assert result.error is None
    assert result.winner == "p1"
    assert result.game["players"][1]["hp"] <= 0


def test_game_be_003_2_s2_end_turn_emits_winner_on_bleeding_out_death(repo):
    # opponent has 1 HP and empty deck → Bleeding Out reduces HP to 0
    repo.save_game("g1", _game(hp_opp=1, opp_deck=[]))
    result = end_turn_handler(game_id="g1", acting_player_id="p1", repo=repo)
    assert result.error is None
    assert result.winner == "p1"
    assert result.game["players"][1]["hp"] == 0


def test_game_be_003_2_s3_actions_rejected_on_finished_game(repo):
    # store an already-finished game
    finished = _game(hp_opp=0, mana=3, hand=[1])
    finished["winner"] = "p1"
    repo.save_game("g1", finished)
    result = play_card_handler(
        game_id="g1", acting_player_id="p1", card_index=0, repo=repo
    )
    assert result.error == "game over"
