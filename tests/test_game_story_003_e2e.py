import sqlite3

import pytest

from game.handlers import end_turn_handler, play_card_handler
from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def _arm(repo, active_hand, active_mana, opp_hp, opp_deck):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    game = match.game
    game["players"][0] = {
        **game["players"][0],
        "hand": active_hand,
        "mana": active_mana,
        "mana_slots": active_mana,
    }
    game["players"][1] = {**game["players"][1], "hp": opp_hp, "deck": opp_deck}
    repo.save_game(game["game_id"], game)
    return game


def test_game_story_003_s1_win_by_card_damage(repo):
    # opponent has 2 HP; active player plays a card of cost 3
    game = _arm(repo, active_hand=[3], active_mana=3, opp_hp=2, opp_deck=[])
    active_id = game["players"][0]["id"]
    result = play_card_handler(
        game_id=game["game_id"], acting_player_id=active_id, card_index=0, repo=repo
    )
    assert result.winner == active_id
    assert result.game["players"][1]["hp"] <= 0


def test_game_story_003_s2_win_by_bleeding_out(repo):
    # opponent has 1 HP and empty deck
    game = _arm(repo, active_hand=[], active_mana=0, opp_hp=1, opp_deck=[])
    active_id = game["players"][0]["id"]
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )
    assert result.winner == active_id
    assert result.game["players"][1]["hp"] == 0
