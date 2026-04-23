# 3. System Scope and Context

## 3.1 System Scope

The Trading Card Game System is responsible for:

- Authenticating players via a JWT signed with a pre-shared key
- Matchmaking: pairing two players into a game session
- Enforcing all game rules (mana, deck, hand, damage, win condition)
- Persisting game state between turns (in SQLite on a Docker volume)
- Broadcasting state updates to both players over WebSocket

Everything outside this boundary — the browser client and the host Docker
daemon — is an external system.

## 3.2 Context Diagram

See [`diagrams/c4-context.svg`](diagrams/c4-context.svg).

## 3.3 External Interfaces

| External System | Direction | Protocol | Purpose |
|----------------|-----------|----------|---------|
| Player (browser) | in/out | WebSocket (`ws://localhost:8000`) | Send game actions; receive state updates |
| Host filesystem | out | Docker volume mount | Persist SQLite database across container restarts |
