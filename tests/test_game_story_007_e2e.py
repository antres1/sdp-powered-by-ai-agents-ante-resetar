import sqlite3

import pytest

from game.handlers import end_turn_handler, rejoin
from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    r = MatchmakingRepository(conn)
    r.init_schema()
    return r


def test_game_story_007_s1_reconnect_with_active_game(repo):
    # GIVEN a game is in progress between two players
    join_queue(player_id="alice", repo=repo, now_epoch=1)
    match = join_queue(player_id="bob", repo=repo, now_epoch=2)
    game = match.game
    game_id = game["game_id"]

    # Advance the game one turn so state has changed
    active_id = game["players"][0]["id"]
    end_turn_handler(game_id=game_id, acting_player_id=active_id, repo=repo)

    # WHEN alice reconnects (simulated by calling rejoin with her player_id)
    result = rejoin(player_id="alice", game_repo=repo)

    # THEN she receives the current game state
    assert result["status"] == "rejoined"
    assert result["game"]["game_id"] == game_id
    player_ids = [p["id"] for p in result["game"]["players"]]
    assert "alice" in player_ids


def test_game_story_007_s2_reconnect_with_no_active_game(repo):
    # GIVEN no game exists for this player
    # WHEN the player attempts to rejoin
    result = rejoin(player_id="alice", game_repo=repo)

    # THEN they are directed to the lobby
    assert result["status"] == "no_active_game"
    assert "game" not in result
