# 8. Cross-cutting Concepts

## 8.1 Authentication & Authorisation

- Authentication happens **once** — on WebSocket connect.
- The `connect` handler extracts the JWT from the query string, validates its signature locally with PyJWT using `JWT_SECRET`, and stores `connectionId → playerId` in SQLite.
- All subsequent actions trust the `connectionId` already stored; no repeated token validation.
- Action handlers verify the acting player is the **active player** in the loaded `GameState` before applying any action.

## 8.2 Error Handling

| Error type | Handling |
|-----------|---------|
| Rule violation (e.g. not enough mana) | Domain raises `RuleViolation`; handler catches and sends `{"error": "..."}` to the acting player only |
| Not your turn | Handler checks active player before calling domain; returns `{"error": "not your turn"}` |
| Stale / missing game state | Handler returns `{"error": "game not found"}` and logs a warning |
| Unhandled exception | Handler logs the traceback to stderr; the WebSocket frame is closed; the process keeps running |

Domain exceptions are **never** propagated as raw Python tracebacks to the client.

## 8.3 Logging & Observability

- The service writes structured JSON logs to stdout using the Python `logging` module.
- Every log entry includes: `gameId`, `playerId`, `action`, `durationMs`.
- Logs are captured by the Docker daemon and viewable via `docker logs <container>`.
- No external tracing or metrics service is used for the kata.

## 8.4 Game State Consistency

- Each game action is a **single SQLite transaction** that reads the current state row, applies the domain function, and writes the new state.
- A `version` column on `games` is checked with an `UPDATE ... WHERE version = :expected` to detect concurrent writes; the second writer gets zero rows affected and retries.
- One game lives in one row; all mutations are atomic within the transaction.

## 8.5 WebSocket Connection Lifecycle

- Each `connections` row carries an `expires_at` column set to `now + 24 h`. Expired rows are pruned on the next connect.
- If the server tries to send a frame on a closed connection, it deletes the stale `connections` row and logs a warning — the action itself is not failed.
