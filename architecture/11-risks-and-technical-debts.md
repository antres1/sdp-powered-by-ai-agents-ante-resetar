# 11. Risks and Technical Debts

## 11.1 Risks

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|-----------|
| R-1 | **Cold start latency** — first Lambda invocation after idle adds 200–500 ms, breaking the 500 ms responsiveness goal | Medium | Medium | Use Lambda Provisioned Concurrency for `PlayCardFunction` and `EndTurnFunction` if p95 breaches threshold; keep deployment package small |
| R-2 | **WebSocket connection loss** — client disconnects mid-game; opponent is stuck | Medium | High | Client implements exponential-backoff reconnect; `$connect` restores session from DynamoDB by `playerId` |
| R-3 | **Concurrent action race** — two actions for the same game arrive simultaneously (e.g. network retry) | Low | High | DynamoDB conditional write (`version` attribute); second write fails and Lambda returns a conflict error |
| R-4 | **Matchmaking queue race** — two `MatchmakingFunction` invocations both claim the same waiting player | Low | Medium | DynamoDB conditional delete on queue item; only one invocation succeeds, the other retries |

## 11.2 Technical Debts

| ID | Debt | Impact | Remediation |
|----|------|--------|------------|
| TD-1 | **No reconnection flow implemented** — client has no logic to re-attach to an in-progress game after disconnect | Player loses game on network blip | Implement `rejoinGame` WebSocket route that restores state from DynamoDB |
| TD-2 | **Shared domain code duplication** — domain layer copied into each Lambda package until a Lambda Layer is set up | Maintenance burden when rules change | Extract domain into a SAM Lambda Layer shared by all functions |
| TD-3 | **No integration tests against real DynamoDB** — only unit tests with in-memory fakes | Adapter bugs may reach production | Add integration tests using DynamoDB Local or `pytest` with `moto` |
| TD-4 | **Single AWS region** — no failover if `eu-central-1` has an outage | Full service unavailability | Acceptable for a kata; multi-region would require DynamoDB Global Tables and Route 53 failover |
