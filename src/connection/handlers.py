from dataclasses import dataclass

import jwt

from connection.repository import Connection, ConnectionRepository

CONNECTION_TTL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class ConnectResult:
    accepted: bool
    player_id: str | None = None


def connect(
    *,
    connection_id: str,
    token: str,
    secret: str,
    repo: ConnectionRepository,
    now_epoch: int,
) -> ConnectResult:
    claims = jwt.decode(token, secret, algorithms=["HS256"])
    player_id = claims["sub"]
    repo.put(
        Connection(
            connection_id=connection_id,
            player_id=player_id,
            expires_at=now_epoch + CONNECTION_TTL_SECONDS,
        )
    )
    return ConnectResult(accepted=True, player_id=player_id)
