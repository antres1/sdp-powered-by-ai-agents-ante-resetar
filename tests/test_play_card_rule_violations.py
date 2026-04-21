import pytest

from domain.game import play_card
from domain.models import GameState, Player, RuleViolationError


def test_game_be_004_1_s1_insufficient_mana_raises_rule_violation():
    # GIVEN a GameState where the active player has mana=2 and hand=[5, 3]
    active = Player(id="p1", hp=30, mana=2, mana_slots=2, hand=[5, 3], deck=[])
    opponent = Player(id="p2", hp=30, mana=0, mana_slots=0, hand=[], deck=[])
    state = GameState(players=[active, opponent], active_player_index=0)

    # WHEN play_card is called with card_index=0 (cost=5, exceeds mana=2)
    # THEN RuleViolationError("not enough mana") is raised
    with pytest.raises(RuleViolationError, match="not enough mana"):
        play_card(state, card_index=0)

    # AND the input state is unchanged
    assert state.players[0].mana == 2
    assert state.players[0].hand == [5, 3]
    assert state.players[1].hp == 30
