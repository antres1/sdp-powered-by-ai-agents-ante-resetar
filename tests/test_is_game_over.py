from domain.game import is_game_over
from domain.models import GameState, Player


def _state(hp_a=30, hp_b=30):
    return GameState(
        players=[
            Player(id="p1", hp=hp_a, mana=0, mana_slots=0, hand=[], deck=[]),
            Player(id="p2", hp=hp_b, mana=0, mana_slots=0, hand=[], deck=[]),
        ],
        active_player_index=0,
    )


def test_game_be_003_1_s1_returns_winner_when_opponent_at_zero_hp():
    state = _state(hp_a=10, hp_b=0)
    assert is_game_over(state) == "p1"


def test_game_be_003_1_s2_returns_none_when_both_players_alive():
    state = _state(hp_a=10, hp_b=10)
    assert is_game_over(state) is None


def test_game_be_003_1_s3_returns_winner_when_hp_negative():
    state = _state(hp_a=10, hp_b=-3)
    assert is_game_over(state) == "p1"
