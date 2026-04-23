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


def _arm_game(repo, opp_deck, opp_hp=30):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    game = match.game
    game["players"][1] = {**game["players"][1], "deck": opp_deck, "hp": opp_hp}
    repo.save_game(game["game_id"], game)
    return game


def test_game_story_005_s1_bleeding_out_reduces_hp_by_1(repo):
    # GIVEN opponent's deck is empty and HP is 30
    game = _arm_game(repo, opp_deck=[])
    active_id = game["players"][0]["id"]

    # WHEN active player ends turn
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )

    # THEN opponent HP reduced by 1, hand size unchanged, active player switches
    assert result.error is None
    assert result.game["players"][1]["hp"] == 29
    opp_hand_before = len(game["players"][1]["hand"])
    assert len(result.game["players"][1]["hand"]) == opp_hand_before
    assert result.game["active_player_index"] == 1


def test_game_story_005_s2_bleeding_out_can_trigger_win_condition(repo):
    # GIVEN opponent has 1 HP and empty deck
    game = _arm_game(repo, opp_deck=[], opp_hp=1)
    active_id = game["players"][0]["id"]

    # WHEN active player ends turn
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )

    # THEN opponent HP drops to 0
    assert result.game["players"][1]["hp"] == 0
