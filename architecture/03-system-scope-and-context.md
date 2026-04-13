# 3. System Scope and Context

## 3.1 System Scope

The Trading Card Game System is responsible for:

- Authenticating players (delegated to Cognito)
- Matchmaking: pairing two players into a game session
- Enforcing all game rules (mana, deck, hand, damage, win condition)
- Persisting game state between turns (via DynamoDB)
- Broadcasting state updates to both players in real time

Everything outside this boundary — the browser client, identity provider, and
database — is an external system.

## 3.2 Context Diagram

See [`diagrams/c4-context.svg`](diagrams/c4-context.svg).

## 3.3 External Interfaces

| External System | Direction | Protocol | Purpose |
|----------------|-----------|----------|---------|
| Player (browser) | in/out | WebSocket (wss://) | Send game actions; receive state updates |
| AWS Cognito | out | HTTPS | Validate JWT tokens on connect |
| Amazon DynamoDB | out | HTTPS (AWS SDK) | Persist and retrieve game state, player sessions, connection IDs |
