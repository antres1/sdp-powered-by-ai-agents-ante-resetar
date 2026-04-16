# GAME-STORY-007: Reconnect Restores In-Progress Game Session

**Architecture Reference**: Section 8.5 — WebSocket Connection Lifecycle; Section 8.1 — Authentication & Authorisation; Section 5.3 — DynamoDB Access Patterns (Connection, Game); Section 9 — ADR-003 (reconnection logic needed in client)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT to reconnect to an in-progress game after a dropped WebSocket connection
SO THAT a temporary network interruption does not forfeit my game

### SCENARIO 1: Reconnecting player receives current game state

**Scenario ID**: GAME-STORY-007-S1

**GIVEN**
* A game is in progress with `GAME#<gameId> / STATE` in DynamoDB
* The player's previous WebSocket connection has dropped
* The player reconnects with a valid JWT

**WHEN**
* The player opens a new WebSocket connection and sends `{"action": "joinQueue"}` or a dedicated `{"action": "rejoin"}`

**THEN**
* The new `connectionId` is stored in DynamoDB, replacing the old one
* The player receives `{"status": "rejoined", "gameState": {...}}` with the current game state
* The opponent is notified that the player has reconnected

### SCENARIO 2: Reconnect with no active game returns to lobby

**Scenario ID**: GAME-STORY-007-S2

**GIVEN**
* A player reconnects with a valid JWT
* No active game exists for this player in DynamoDB

**WHEN**
* The player sends `{"action": "rejoin"}`

**THEN**
* The player receives `{"status": "no_active_game"}`
* The client shows the lobby screen

---

## Frontend Sub-Stories

### GAME-FE-007.1: Automatic reconnection with session restore

AS A player
I WANT the client to automatically attempt reconnection after a dropped connection and restore the game board if a game is in progress
SO THAT brief network interruptions are transparent

#### SCENARIO 1: Client reconnects and restores game board

**Scenario ID**: GAME-FE-007.1-S1

**GIVEN**
* The WebSocket `onclose` event fires unexpectedly during a game
* The player still has a valid JWT

**WHEN**
* The client reconnects (with exponential backoff, max 3 attempts)

**THEN**
* A new WebSocket connection is established
* The client sends `{"action": "rejoin"}`
* On receiving `{"status": "rejoined", "gameState": {...}}`, the game board is restored to the current state

#### SCENARIO 2: Client shows lobby after failed reconnect or no active game

**Scenario ID**: GAME-FE-007.1-S2

**GIVEN**
* All reconnection attempts fail or the server returns `{"status": "no_active_game"}`

**WHEN**
* The client processes the response

**THEN**
* The "Connection lost" overlay is dismissed
* The lobby screen is shown

---

## Backend Sub-Stories

### GAME-BE-007.1: RejoinFunction looks up active game and sends current state

**Architecture Reference**: Section 5.1 — ConnectFunction (extended); Section 8.1 — Authentication & Authorisation; Section 5.3 — DynamoDB Access Patterns

AS A system
I WANT a `rejoin` handler to update the connection mapping and return the current game state to the reconnecting player
SO THAT reconnection is handled server-side without requiring a new matchmaking flow

#### SCENARIO 1: Active game found — connection updated and state returned

**Scenario ID**: GAME-BE-007.1-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists where `player.id == playerId`
* The player reconnects with a new `connectionId`

**WHEN**
* The `rejoin` handler is invoked

**THEN**
* The `CONN#<newConnectionId> / PLAYER` item is written (new mapping)
* The old `CONN#<oldConnectionId> / PLAYER` item is deleted
* The game state item is updated with the new `connectionId` for this player
* The player receives `{"status": "rejoined", "gameState": {...}}`
* The opponent receives `{"status": "opponent_reconnected"}`

#### SCENARIO 2: No active game — player directed to lobby

**Scenario ID**: GAME-BE-007.1-S2

**GIVEN**
* No game item exists for the reconnecting player

**WHEN**
* The `rejoin` handler is invoked

**THEN**
* The player receives `{"status": "no_active_game"}`
* No game item is written or modified

---

## Infrastructure Sub-Stories

### GAME-INFRA-007.1: Deploy RejoinFunction Lambda with `rejoin` route

**Architecture Reference**: Section 5.1 — Building Block View; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT a RejoinFunction Lambda deployed via SAM with a `rejoin` WebSocket route
SO THAT reconnecting players have a compute target to restore their session

#### SCENARIO 1: Lambda deployed and invocable

**Scenario ID**: GAME-INFRA-007.1-S1

**GIVEN**
* `template.yaml` defines `RejoinFunction` with `Runtime: python3.12` and the `rejoin` route integration

**WHEN**
* `sam deploy` completes

**THEN**
* The Lambda exists and a synthetic invocation returns without a 5xx error
* The log group `/aws/lambda/RejoinFunction` exists

---

### GAME-INFRA-007.2: DynamoDB — connection update and game state lookup for rejoin

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Connection, Game)

AS A DevOps engineer
I WANT RejoinFunction's IAM role to allow `GetItem`, `PutItem`, and `DeleteItem` on `GameTable`
SO THAT it can update the connection mapping and read the current game state

#### SCENARIO 1: Connection item updated and game state retrieved

**Scenario ID**: GAME-INFRA-007.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item and an old `CONN#<oldConnId> / PLAYER` item exist
* RejoinFunction's execution role has `GetItem`, `PutItem`, `DeleteItem` on `GameTable`

**WHEN**
* RejoinFunction executes

**THEN**
* The old connection item is deleted
* A new `CONN#<newConnId> / PLAYER` item is written
* The game state is retrieved without `AccessDeniedException`

---

### GAME-INFRA-007.3: WebSocket — rejoin route delivers event to Lambda

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the `rejoin` WebSocket route integrated with RejoinFunction
SO THAT reconnection frames are routed to the correct Lambda

#### SCENARIO 1: `rejoin` route delivers event to Lambda

**Scenario ID**: GAME-INFRA-007.3-S1

**GIVEN**
* `template.yaml` defines a `rejoin` route pointing to `RejoinFunction`
* The stack is deployed

**WHEN**
* A reconnected client sends `{"action": "rejoin"}`

**THEN**
* API Gateway invokes `RejoinFunction` with `connectionId` and the message body

---

### GAME-INFRA-007.4: CloudWatch — reconnection events logged

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT reconnection events to appear in structured logs
SO THAT reconnection frequency and failures are observable

#### SCENARIO 1: Structured log emitted on rejoin

**Scenario ID**: GAME-INFRA-007.4-S1

**GIVEN**
* RejoinFunction uses AWS Lambda Powertools `Logger`
* A rejoin event is processed

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry in `/aws/lambda/RejoinFunction` contains `playerId`, `gameId` (or null), `event: "rejoin"`, and `durationMs`

---

## Implementation Order

```
GAME-INFRA-007.2 (DynamoDB IAM for connection update + game lookup)
  → GAME-INFRA-007.1 (RejoinFunction Lambda deploy)
  → GAME-INFRA-007.3 (rejoin route)
  → GAME-INFRA-007.4 (logging)
  → GAME-BE-007.1 (rejoin handler logic)
  → GAME-FE-007.1 (auto-reconnect with backoff + game board restore)
  → GAME-STORY-007 (E2E: drop connection mid-game, reconnect, verify game state restored)
```
