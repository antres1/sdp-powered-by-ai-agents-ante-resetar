# 11. Risks and Technical Debts

## 11.1 Risks

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|-----------|
| R-1 | **Container restart loses open sockets** — any crash or redeploy drops all in-flight games | Medium | Medium | Persist game state in SQLite; client reconnects and restores session by `playerId` |
| R-2 | **WebSocket connection loss** — client disconnects mid-game; opponent is stuck | Medium | High | Client implements exponential-backoff reconnect; on connect, the server restores session from SQLite by `playerId` |
| R-3 | **Concurrent action race** — two actions for the same game arrive simultaneously (e.g. network retry) | Low | High | SQLite `UPDATE ... WHERE version = :expected`; second write affects zero rows and the handler returns a conflict error |
| R-4 | **Matchmaking queue race** — two `joinQueue` handlers both claim the same waiting player | Low | Medium | SQLite `DELETE ... WHERE player_id = ?` inside a transaction; only one deleter proceeds, the other retries |

## 11.2 Technical Debts

| ID | Debt | Impact | Remediation |
|----|------|--------|------------|
| TD-1 | **No reconnection flow implemented** — client has no logic to re-attach to an in-progress game after disconnect | Player loses game on network blip | Implement `rejoinGame` WebSocket action that restores state from SQLite |
| TD-2 | **Single-writer SQLite** — only one container can safely write at a time | Blocks horizontal scale-out | Acceptable for a kata; swap to PostgreSQL in a separate container if multi-instance is ever needed |
| TD-3 | **No integration tests against a real socket** — only unit tests with in-memory fakes | Adapter bugs may hide behind the fakes | Add `pytest` tests that spin up the WebSocket server in-process and connect with a real client |
| TD-4 | **Single container** — no redundancy | Host outage = service outage | Acceptable for a kata run locally |
