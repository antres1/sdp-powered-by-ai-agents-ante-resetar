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


def _deal_hand(repo, game_id: str, hand: list[int], mana: int) -> None:
    game = repo.get_game(game_id)
    game["players"][0] = {
        **game["players"][0],
        "hand": hand,
        "mana": mana,
        "mana_slots": mana,
    }
    repo.save_game(game_id, game)


def test_game_story_001_s1_valid_play_updates_game(repo):
    # GIVEN a game created by matchmaking for A and B
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    gid = match.game["game_id"]
    active_id = match.game["players"][0]["id"]
    _deal_hand(repo, gid, hand=[1, 3, 2], mana=4)

    # WHEN the active player plays index 1 (cost=3)
    result = play_card_handler(
        game_id=gid, acting_player_id=active_id, card_index=1, repo=repo
    )

    # THEN the state reflects the play and is persisted
    assert result.error is None
    assert result.game["players"][0]["mana"] == 1
    assert result.game["players"][0]["hand"] == [1, 2]
    assert result.game["players"][1]["hp"] == 27


def test_game_story_001_s2_insufficient_mana_rejected(repo):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    gid = match.game["game_id"]
    active_id = match.game["players"][0]["id"]
    _deal_hand(repo, gid, hand=[5, 3], mana=2)

    result = play_card_handler(
        game_id=gid, acting_player_id=active_id, card_index=0, repo=repo
    )
    assert result.error == "not enough mana"
    # state unchanged
    assert repo.get_game(gid)["players"][0]["mana"] == 2


def test_game_story_001_s3_wrong_player_rejected(repo):
    join_queue(player_id="A", repo=repo, now_epoch=1)
    match = join_queue(player_id="B", repo=repo, now_epoch=2)
    gid = match.game["game_id"]
    inactive_id = match.game["players"][1]["id"]

    result = play_card_handler(
        game_id=gid, acting_player_id=inactive_id, card_index=0, repo=repo
    )
    assert result.error == "not your turn"
