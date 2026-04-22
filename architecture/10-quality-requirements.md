# 10. Quality Requirements

## 10.1 Quality Tree

| Quality Goal | Scenario | Measure |
|-------------|---------|---------|
| **Correctness** | A player attempts to play a card they cannot afford | System rejects the action; game state unchanged |
| **Correctness** | A player draws from an empty deck | Bleeding Out applies exactly 1 damage; no crash |
| **Correctness** | A player draws when hand is full | Card is discarded (Overload); hand size stays at 5 |
| **Responsiveness** | Player plays a card | Opponent sees updated state within 500 ms (p95) |
| **Responsiveness** | Player connects and joins queue | Match found and both players notified within 1 s |
| **Testability** | Developer runs the test suite | `docker run --rm tcg-tests` passes all domain rule tests with no external dependencies |
| **Reproducibility** | Developer checks out the repo on a clean machine | `docker build . && docker run` produces a working service |
| **Operability** | An action handler throws an unhandled exception | Error appears in `docker logs` with `gameId` and stack trace within 1 s |

## 10.2 Quality Scenarios (detail)

### Correctness — Rule Enforcement
- All game rules are implemented as pure functions.
- Each rule has dedicated unit tests covering happy path and every edge case from the kata (Bleeding Out, Overload, mana cap at 10, hand limit of 5, deck of 20 cards).
- A rule violation must never mutate persisted state.

### Responsiveness — Real-time Push
- After any action handler completes, the server pushes the updated frame to both players' open sockets before the handler returns.
- Target: handler total duration ≤ 50 ms (p95) on a developer machine.

### Testability — No-infra Domain Tests
- `pytest` runs the full domain test suite in < 5 s with no network calls.
- Action handlers are tested with injected in-memory fakes for `GameRepository` and `PlayerNotifier`.

### Operability — Observability
- The service emits structured JSON logs to stdout including `gameId`, `playerId`, `action`, `durationMs`.
- Logs are captured by Docker and viewable via `docker logs <container>`.
