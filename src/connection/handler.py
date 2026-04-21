from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt

from connection.repository import ConnectionRecord, InMemoryConnectionRepository


def connect(
    event: dict,
    repo: InMemoryConnectionRepository,
    secret: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> dict:
    connection_id = event["requestContext"]["connectionId"]
    token = event["queryStringParameters"]["token"]

    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return {"statusCode": 401}

    player_id = claims["sub"]

    repo.put(
        ConnectionRecord(
            connection_id=connection_id,
            player_id=player_id,
            expires_at=now() + timedelta(hours=24),
        )
    )
    return {"statusCode": 200}
