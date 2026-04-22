import uuid
from dataclasses import dataclass

from matchmaking.repository import MatchmakingRepository, QueueEntry

# Simple fixed starting deck: costs 0..7. Same for both players for determinism.
STARTING_DECK = [0, 1, 1, 2, 2, 3, 3, 4, 5, 7]
STARTING_HAND_SIZE = 3


def _deal(deck: list[int], n: int) -> tuple[list[int], list[int]]:
    return deck[:n], deck[n:]


@dataclass(frozen=True)
class JoinQueueResult:
    status: str
    game: dict | None = None


def _player(player_id: str) -> dict:
    hand, deck = _deal(list(STARTING_DECK), STARTING_HAND_SIZE)
    return {
        "id": player_id,
        "hp": 30,
        "mana": 0,
        "mana_slots": 0,
        "hand": hand,
        "deck": deck,
    }


def _initial_game(game_id: str, player_a: str, player_b: str) -> dict:
    # Player A goes first; their opening turn is already begun (1 mana refilled).
    first = _player(player_a)
    first["mana_slots"] = 1
    first["mana"] = 1
    return {
        "game_id": game_id,
        "player_ids": [player_a, player_b],
        "active_player_index": 0,
        "players": [first, _player(player_b)],
    }


def join_queue(
    *,
    player_id: str,
    repo: MatchmakingRepository,
    now_epoch: int,
) -> JoinQueueResult:
    opponent = repo.pop_waiting()
    if opponent is None:
        repo.enqueue(QueueEntry(player_id=player_id, joined_at=now_epoch))
        return JoinQueueResult(status="waiting")

    game_id = str(uuid.uuid4())
    game = _initial_game(game_id, opponent.player_id, player_id)
    repo.save_game(game_id, game)
    return JoinQueueResult(status="matched", game=game)
