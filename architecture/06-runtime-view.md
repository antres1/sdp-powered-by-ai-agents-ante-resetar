# 6. Runtime View

## Scenario 1: Player Connect & Matchmaking

See [`diagrams/seq-matchmaking.svg`](diagrams/seq-matchmaking.svg).

1. Player opens WebSocket connection with JWT in the query string.
2. `ConnectFunction` validates the token with Cognito and stores `connectionId → playerId` in DynamoDB.
3. Player sends `joinQueue`; `MatchmakingFunction` writes them to the queue.
4. If an opponent is already waiting, both queue entries are deleted, an initial `GameState` is created, and both players are notified via the Management API.

## Scenario 2: Play Card

See [`diagrams/seq-play-card.svg`](diagrams/seq-play-card.svg).

1. Active player sends `playCard` with a card index.
2. `PlayCardFunction` loads `GameState` from DynamoDB and delegates to `Game Rules`.
3. On a rule violation (insufficient mana) only the acting player receives an error.
4. On success, the new state is persisted and pushed to both players.
5. If the opponent's health drops to ≤ 0, a `game_over` message is sent to both.

## Scenario 3: End Turn

See [`diagrams/seq-end-turn.svg`](diagrams/seq-end-turn.svg).

1. Active player sends `endTurn`.
2. `EndTurnFunction` loads state and calls `end_turn()` in the domain layer.
3. Domain applies: increment mana slots → refill mana → draw card (with Bleeding Out / Overload checks) → switch active player.
4. New state is persisted and pushed to both players.
5. If Bleeding Out reduced the drawing player to ≤ 0 HP, `game_over` is broadcast.
