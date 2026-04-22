from dataclasses import replace

from domain.models import GameState, RuleViolationError


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
