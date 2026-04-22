from dataclasses import dataclass

from matchmaking.repository import MatchmakingRepository, QueueEntry


@dataclass(frozen=True)
class JoinQueueResult:
    status: str
    game: dict | None = None


def join_queue(
    *,
    player_id: str,
    repo: MatchmakingRepository,
    now_epoch: int,
) -> JoinQueueResult:
    repo.enqueue(QueueEntry(player_id=player_id, joined_at=now_epoch))
    return JoinQueueResult(status="waiting")
