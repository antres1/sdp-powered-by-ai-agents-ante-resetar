# 10. Quality Requirements

## 10.1 Quality Tree

| Quality Goal | Scenario | Measure |
|-------------|---------|---------|
| **Correctness** | A player attempts to play a card they cannot afford | System rejects the action; game state unchanged |
| **Correctness** | A player draws from an empty deck | Bleeding Out applies exactly 1 damage; no crash |
| **Correctness** | A player draws when hand is full | Card is discarded (Overload); hand size stays at 5 |
| **Responsiveness** | Player plays a card | Opponent sees updated state within 500 ms (p95) |
| **Responsiveness** | Player connects and joins queue | Match found and both players notified within 1 s |
| **Testability** | Developer runs the test suite locally | All domain rule tests pass without AWS credentials |
| **Scalability** | 100 concurrent games in progress | No provisioned capacity required; DynamoDB and Lambda scale automatically |
| **Operability** | A Lambda throws an unhandled exception | Error appears in CloudWatch with `gameId` and stack trace within 30 s |
| **Operability** | A new developer deploys the stack | `sam deploy` completes successfully from a clean AWS account |

## 10.2 Quality Scenarios (detail)

### Correctness — Rule Enforcement
- All game rules are implemented as pure functions.
- Each rule has dedicated unit tests covering happy path and every edge case from the kata (Bleeding Out, Overload, mana cap at 10, hand limit of 5, deck of 20 cards).
- A rule violation must never mutate persisted state.

### Responsiveness — Real-time Push
- After any game action Lambda completes, `postToConnection` is called for both players before the Lambda returns.
- Target: action Lambda total duration ≤ 300 ms (p95) excluding cold start.

### Testability — No-infra Domain Tests
- `pytest` runs the full domain test suite in < 5 s with no network calls.
- Lambda handlers are tested with injected in-memory fakes for `GameRepository` and `PlayerNotifier`.

### Operability — Observability
- Every Lambda emits structured JSON logs (Lambda Powertools) including `gameId`, `playerId`, `action`, `durationMs`.
- X-Ray traces link API Gateway → Lambda → DynamoDB for every request.
