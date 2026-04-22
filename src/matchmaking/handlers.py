import uuid
from dataclasses import dataclass

from matchmaking.repository import MatchmakingRepository, QueueEntry


@dataclass(frozen=True)
class JoinQueueResult:
    status: str
    game: dict | None = None


def _initial_game(game_id: str, player_a: str, player_b: str) -> dict:
    return {
        "game_id": game_id,
        "player_ids": [player_a, player_b],
        "active_player_index": 0,
        "players": [
            {
                "id": player_a,
                "hp": 30,
                "mana": 0,
                "mana_slots": 0,
                "hand": [],
                "deck": [],
            },
            {
                "id": player_b,
                "hp": 30,
                "mana": 0,
                "mana_slots": 0,
                "hand": [],
                "deck": [],
            },
        ],
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
