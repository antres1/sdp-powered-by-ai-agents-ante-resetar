import pytest

from domain.game import play_card
from domain.models import GameState, Player, RuleViolationError


def test_game_story_001_s3_inactive_player_cannot_play():
    # GIVEN it is player 0's turn but player 1 tries to play
    active = Player(id="p1", hp=30, mana=10, mana_slots=10, hand=[1, 2], deck=[])
    inactive = Player(id="p2", hp=30, mana=10, mana_slots=10, hand=[3, 4], deck=[])
    state = GameState(players=[active, inactive], active_player_index=0)

    # WHEN play_card is called with acting_player_id of the inactive player
    # THEN a RuleViolationError "not your turn" is raised
    with pytest.raises(RuleViolationError, match="not your turn"):
        play_card(state, card_index=0, acting_player_id="p2")

    # AND state is unchanged
    assert state.players[0].hand == [1, 2]
    assert state.players[1].hand == [3, 4]
