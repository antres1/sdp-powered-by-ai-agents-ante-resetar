import sqlite3

import pytest

from game.handlers import play_card_handler
from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def _arm(repo, hand, mana):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    game = match.game
    game["players"][0] = {
        **game["players"][0],
        "hand": hand,
        "mana": mana,
        "mana_slots": mana,
    }
    repo.save_game(game["game_id"], game)
    return game


def test_game_story_004_s1_insufficient_mana_rejected(repo):
    # GIVEN the active player has 2 mana and a card costing 5
    game = _arm(repo, hand=[5], mana=2)
    active_id = game["players"][0]["id"]

    # WHEN playCard runs
    result = play_card_handler(
        game_id=game["game_id"], acting_player_id=active_id, card_index=0, repo=repo
    )

    # THEN typed error is returned, game state is unchanged
    assert result.error == "not enough mana"
    assert result.game is None
    stored = repo.get_game(game["game_id"])
    assert stored["players"][0]["mana"] == 2
    assert stored["players"][0]["hand"] == [5]


def test_game_story_004_s2_invalid_card_index_rejected(repo):
    # GIVEN the active player has a 2-card hand (indices 0 and 1)
    game = _arm(repo, hand=[1, 2], mana=10)
    active_id = game["players"][0]["id"]

    # WHEN playCard runs with index 5
    result = play_card_handler(
        game_id=game["game_id"], acting_player_id=active_id, card_index=5, repo=repo
    )

    # THEN typed error is returned, state unchanged
    assert result.error == "invalid card index"
    assert result.game is None
    stored = repo.get_game(game["game_id"])
    assert stored["players"][0]["hand"] == [1, 2]
