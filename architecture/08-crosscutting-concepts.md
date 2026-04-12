# 8. Cross-cutting Concepts

## 8.1 Authentication & Authorisation

- Authentication happens **once** — on WebSocket `$connect`.
- `ConnectFunction` extracts the JWT from the query string, calls Cognito to validate it, and stores `connectionId → playerId` in DynamoDB.
- All subsequent Lambda invocations trust the `connectionId` already stored; no repeated token validation.
- Game-action Lambdas verify the acting player is the **active player** in the loaded `GameState` before applying any action.

## 8.2 Error Handling

| Error type | Handling |
|-----------|---------|
| Rule violation (e.g. not enough mana) | Domain raises `RuleViolation`; handler catches and sends `{"error": "..."}` to the acting player only |
| Not your turn | Handler checks active player before calling domain; returns `{"error": "not your turn"}` |
| Stale / missing game state | Handler returns `{"error": "game not found"}` and logs a warning |
| Unhandled exception | Lambda returns HTTP 500; API Gateway closes the frame; CloudWatch captures the traceback |

Domain exceptions are **never** propagated as raw Python tracebacks to the client.

## 8.3 Logging & Observability

- All Lambdas use **AWS Lambda Powertools** (`Logger`, `Tracer`).
- Every log entry includes: `gameId`, `playerId`, `action`, `durationMs`.
- Structured JSON logs flow to CloudWatch Logs; a log group per function.
- X-Ray tracing enabled on all Lambdas and DynamoDB calls for latency analysis.

## 8.4 Game State Consistency

- Each game action is a **single DynamoDB `PutItem`** (full state replacement).
- DynamoDB conditional writes (`attribute_exists(PK)`) guard against writing to a non-existent game.
- No distributed transactions needed — one game lives in one item; all mutations are atomic at the item level.

## 8.5 WebSocket Connection Lifecycle

- `connectionId` items in DynamoDB carry a **TTL of 24 hours** to auto-expire stale connections.
- If `postToConnection` returns `GoneException` (client disconnected), the Lambda deletes the connection item and logs a warning — it does not fail the action.
