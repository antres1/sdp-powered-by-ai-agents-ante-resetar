from domain.game import play_card
from domain.models import GameState, Player


def test_game_be_001_2_s1_valid_play_reduces_mana_and_deals_damage():
    # GIVEN a GameState where active player has mana=4, hand=[1, 3, 2]
    active = Player(id="p1", hp=30, mana=4, mana_slots=4, hand=[1, 3, 2], deck=[])
    opponent = Player(id="p2", hp=30, mana=0, mana_slots=0, hand=[], deck=[])
    state = GameState(players=[active, opponent], active_player_index=0)

    # WHEN play_card is called with card_index=1 (cost=3)
    new_state = play_card(state, card_index=1)

    # THEN active player mana=1, hand=[1, 2]; opponent HP=27; input state unchanged
    new_active = new_state.players[0]
    new_opponent = new_state.players[1]

    assert new_active.mana == 1
    assert new_active.hand == [1, 2]
    assert new_opponent.hp == 27

    # input state is unchanged (immutability)
    assert state.players[0].mana == 4
    assert state.players[0].hand == [1, 3, 2]
    assert state.players[1].hp == 30
