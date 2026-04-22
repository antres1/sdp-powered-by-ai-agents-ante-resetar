from dataclasses import replace

from domain.models import GameState, RuleViolationError


def play_card(state: GameState, card_index: int) -> GameState:
    i = state.active_player_index
    active = state.players[i]
    opponent = state.players[1 - i]

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
