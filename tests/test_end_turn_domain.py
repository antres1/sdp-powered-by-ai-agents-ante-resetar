from domain.game import end_turn
from domain.models import GameState, Player


def _state(
    active_hand=None,
    opp_deck=None,
    opp_hand=None,
    opp_mana_slots=3,
    opp_hp=30,
):
    active = Player(
        id="p1", hp=30, mana=0, mana_slots=0, hand=list(active_hand or []), deck=[]
    )
    opp = Player(
        id="p2",
        hp=opp_hp,
        mana=0,
        mana_slots=opp_mana_slots,
        hand=list(opp_hand or []),
        deck=list(opp_deck or []),
    )
    return GameState(players=[active, opp], active_player_index=0)


def test_game_story_002_s1_normal_end_turn_opponent_draws_and_becomes_active():
    state = _state(opp_deck=[7, 8], opp_hand=[1], opp_mana_slots=3)
    new_state = end_turn(state)
    opp = new_state.players[1]
    assert opp.mana_slots == 4
    assert opp.mana == 4
    assert opp.hand == [1, 7]  # top of deck drawn
    assert opp.deck == [8]
    assert new_state.active_player_index == 1


def test_game_story_002_s2_bleeding_out_on_empty_deck():
    state = _state(opp_deck=[], opp_hand=[1], opp_mana_slots=3, opp_hp=30)
    new_state = end_turn(state)
    opp = new_state.players[1]
    assert opp.hp == 29
    assert opp.hand == [1]
    assert opp.mana_slots == 4
    assert opp.mana == 4
    assert new_state.active_player_index == 1


def test_game_story_002_s3_overload_discards_when_hand_full():
    state = _state(opp_deck=[9, 8], opp_hand=[1, 2, 3, 4, 5], opp_mana_slots=3)
    new_state = end_turn(state)
    opp = new_state.players[1]
    assert len(opp.hand) == 5
    assert opp.hand == [1, 2, 3, 4, 5]  # no new card added
    assert opp.deck == [8]  # top card discarded
    assert new_state.active_player_index == 1


def test_game_story_002_s4_mana_slots_capped_at_10():
    state = _state(opp_deck=[1], opp_hand=[], opp_mana_slots=10)
    new_state = end_turn(state)
    opp = new_state.players[1]
    assert opp.mana_slots == 10
    assert opp.mana == 10
