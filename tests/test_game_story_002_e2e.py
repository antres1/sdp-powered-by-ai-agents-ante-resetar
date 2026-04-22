import sqlite3

import pytest

from game.handlers import end_turn_handler
from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def _arm_game(repo, opp_deck, opp_hand, opp_slots=3):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    game = match.game
    game["players"][1] = {
        **game["players"][1],
        "deck": opp_deck,
        "hand": opp_hand,
        "mana_slots": opp_slots,
    }
    repo.save_game(game["game_id"], game)
    return game


def test_game_story_002_s1_normal_end_turn(repo):
    game = _arm_game(repo, opp_deck=[7], opp_hand=[])
    active_id = game["players"][0]["id"]
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )
    assert result.error is None
    assert result.game["active_player_index"] == 1
    assert result.game["players"][1]["mana_slots"] == 4
    assert result.game["players"][1]["hand"] == [7]


def test_game_story_002_s2_bleeding_out(repo):
    game = _arm_game(repo, opp_deck=[], opp_hand=[])
    active_id = game["players"][0]["id"]
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )
    assert result.game["players"][1]["hp"] == 29


def test_game_story_002_s3_overload_discards(repo):
    game = _arm_game(repo, opp_deck=[9, 8], opp_hand=[1, 2, 3, 4, 5])
    active_id = game["players"][0]["id"]
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )
    assert len(result.game["players"][1]["hand"]) == 5
    assert result.game["players"][1]["deck"] == [8]


def test_game_story_002_s4_wrong_player_rejected(repo):
    game = _arm_game(repo, opp_deck=[7], opp_hand=[])
    inactive_id = game["players"][1]["id"]
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=inactive_id, repo=repo
    )
    assert result.error == "not your turn"
