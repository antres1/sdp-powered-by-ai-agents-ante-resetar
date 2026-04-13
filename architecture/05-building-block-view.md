# 5. Building Block View

## 5.1 Level 1 — Containers

See [`diagrams/c4-container.svg`](diagrams/c4-container.svg).

| Container | Technology | Responsibility |
|-----------|-----------|---------------|
| Web Client | HTML/JS | Game UI; owns WebSocket lifecycle |
| API Gateway | AWS WebSocket API | Routes frames to Lambdas by action route |
| ConnectFunction | Python / Lambda | Validates JWT via Cognito, stores `connectionId` |
| DisconnectFunction | Python / Lambda | Cleans up `connectionId` on disconnect |
| MatchmakingFunction | Python / Lambda | Pairs two waiting players, creates initial `GameState` |
| PlayCardFunction | Python / Lambda | Applies a card-play action, enforces mana/hand rules |
| EndTurnFunction | Python / Lambda | Advances turn: refills mana, draws card, switches player |
| Amazon DynamoDB | AWS managed | Single table for Players, Games, Connections |

## 5.2 Level 2 — Components (Game Engine Lambdas)

See [`diagrams/c4-component.svg`](diagrams/c4-component.svg).

Each game-action Lambda (PlayCard, EndTurn) is structured identically:

| Component | Type | Responsibility |
|-----------|------|---------------|
| Lambda Handler | Adapter (in) | Parses WebSocket event body, invokes use case |
| Game Use Case | Application | Orchestrates: load → apply → persist → notify |
| GameState | Domain (value object) | Immutable snapshot: health, mana, hand, deck, active player |
| Game Rules | Domain (pure functions) | Mana check, Bleeding Out, Overload, win condition |
| GameRepository | Adapter (out) | DynamoDB `get_game()` / `save_game()` |
| PlayerNotifier | Adapter (out) | API Gateway Management API `post_to_connection()` |

## 5.3 DynamoDB Access Patterns

| Entity | PK | SK | Notes |
|--------|----|----|-------|
| Game | `GAME#<gameId>` | `STATE` | Full game state JSON |
| Connection | `CONN#<connectionId>` | `PLAYER` | Maps connectionId → playerId |
| Queue entry | `QUEUE` | `PLAYER#<playerId>` | Waiting-for-match players |
