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


def _arm_game(repo, opp_deck, opp_hand):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    game = match.game
    game["players"][1] = {**game["players"][1], "deck": opp_deck, "hand": opp_hand}
    repo.save_game(game["game_id"], game)
    return game


def test_game_story_006_s1_drawn_card_discarded_when_hand_is_full(repo):
    # GIVEN opponent's hand has 5 cards and deck is non-empty
    game = _arm_game(repo, opp_deck=[9, 8], opp_hand=[1, 2, 3, 4, 5])
    active_id = game["players"][0]["id"]

    # WHEN active player ends turn
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )

    # THEN top card removed from deck, hand size remains 5
    assert result.error is None
    assert len(result.game["players"][1]["hand"]) == 5
    assert result.game["players"][1]["deck"] == [8]


def test_game_story_006_s2_normal_draw_when_hand_has_fewer_than_5_cards(repo):
    # GIVEN opponent's hand has 4 cards and deck is non-empty
    game = _arm_game(repo, opp_deck=[9, 8], opp_hand=[1, 2, 3, 4])
    active_id = game["players"][0]["id"]

    # WHEN active player ends turn
    result = end_turn_handler(
        game_id=game["game_id"], acting_player_id=active_id, repo=repo
    )

    # THEN card moved to hand, hand size becomes 5
    assert result.error is None
    assert len(result.game["players"][1]["hand"]) == 5
    assert result.game["players"][1]["deck"] == [8]
