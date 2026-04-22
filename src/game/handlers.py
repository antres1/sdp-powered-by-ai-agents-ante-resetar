from dataclasses import dataclass

from domain.game import end_turn, is_game_over, play_card
from domain.models import GameState, Player, RuleViolationError
from matchmaking.repository import MatchmakingRepository


@dataclass(frozen=True)
class PlayCardResult:
    game: dict | None = None
    error: str | None = None
    winner: str | None = None


@dataclass(frozen=True)
class EndTurnResult:
    game: dict | None = None
    error: str | None = None
    winner: str | None = None


def _dict_to_state(d: dict) -> GameState:
    players = [
        Player(
            id=p["id"],
            hp=p["hp"],
            mana=p["mana"],
            mana_slots=p["mana_slots"],
            hand=list(p["hand"]),
            deck=list(p["deck"]),
        )
        for p in d["players"]
    ]
    return GameState(players=players, active_player_index=d["active_player_index"])


def _state_to_dict(game_id: str, state: GameState, player_ids: list[str]) -> dict:
    return {
        "game_id": game_id,
        "player_ids": player_ids,
        "active_player_index": state.active_player_index,
        "players": [
            {
                "id": p.id,
                "hp": p.hp,
                "mana": p.mana,
                "mana_slots": p.mana_slots,
                "hand": list(p.hand),
                "deck": list(p.deck),
            }
            for p in state.players
        ],
    }


def play_card_handler(
    *,
    game_id: str,
    acting_player_id: str,
    card_index: int,
    repo: MatchmakingRepository,
) -> PlayCardResult:
    stored = repo.get_game(game_id)
    if stored is None:
        return PlayCardResult(error="game not found")
    if stored.get("winner"):
        return PlayCardResult(error="game over")

    state = _dict_to_state(stored)
    try:
        new_state = play_card(
            state, card_index=card_index, acting_player_id=acting_player_id
        )
    except RuleViolationError as exc:
        return PlayCardResult(error=str(exc))

    new_dict = _state_to_dict(game_id, new_state, stored["player_ids"])
    winner = is_game_over(new_state)
    if winner is not None:
        new_dict["winner"] = winner
    repo.save_game(game_id, new_dict)
    return PlayCardResult(game=new_dict, winner=winner)


def end_turn_handler(
    *,
    game_id: str,
    acting_player_id: str,
    repo: MatchmakingRepository,
) -> EndTurnResult:
    stored = repo.get_game(game_id)
    if stored is None:
        return EndTurnResult(error="game not found")
    if stored.get("winner"):
        return EndTurnResult(error="game over")

    state = _dict_to_state(stored)
    active = state.players[state.active_player_index]
    if acting_player_id != active.id:
        return EndTurnResult(error="not your turn")

    new_state = end_turn(state)
    new_dict = _state_to_dict(game_id, new_state, stored["player_ids"])
    winner = is_game_over(new_state)
    if winner is not None:
        new_dict["winner"] = winner
    repo.save_game(game_id, new_dict)
    return EndTurnResult(game=new_dict, winner=winner)
