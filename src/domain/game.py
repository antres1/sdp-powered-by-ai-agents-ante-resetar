from dataclasses import replace

from domain.models import GameState, RuleViolationError

MAX_MANA_SLOTS = 10
MAX_HAND_SIZE = 5


def play_card(
    state: GameState,
    card_index: int,
    acting_player_id: str | None = None,
) -> GameState:
    i = state.active_player_index
    active = state.players[i]
    opponent = state.players[1 - i]

    if acting_player_id is not None and acting_player_id != active.id:
        raise RuleViolationError("not your turn")

    if card_index < 0 or card_index >= len(active.hand):
        raise RuleViolationError("invalid card index")

    cost = active.hand[card_index]

    if active.mana < cost:
        raise RuleViolationError("not enough mana")

    new_hand = active.hand[:card_index] + active.hand[card_index + 1 :]
    new_active = replace(active, mana=active.mana - cost, hand=new_hand)
    new_opponent = replace(opponent, hp=opponent.hp - cost)

    new_players = [new_active, new_opponent] if i == 0 else [new_opponent, new_active]
    return replace(state, players=new_players)


def end_turn(state: GameState) -> GameState:
    i = state.active_player_index
    opp = state.players[1 - i]

    new_slots = min(opp.mana_slots + 1, MAX_MANA_SLOTS)
    new_mana = new_slots
    new_hand = list(opp.hand)
    new_deck = list(opp.deck)
    new_hp = opp.hp

    if not new_deck:
        new_hp -= 1
    else:
        drawn = new_deck.pop(0)
        if len(new_hand) < MAX_HAND_SIZE:
            new_hand.append(drawn)
        # else Overload: drawn card is discarded

    new_opp = replace(
        opp,
        mana_slots=new_slots,
        mana=new_mana,
        hand=new_hand,
        deck=new_deck,
        hp=new_hp,
    )
    new_players = list(state.players)
    new_players[1 - i] = new_opp
    return replace(state, players=new_players, active_player_index=1 - i)
