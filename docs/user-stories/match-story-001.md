# MATCH-STORY-001: Player Joins Queue and Gets Matched

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking); Section 5.1 — Building Block View (MatchmakingFunction); Section 5.3 — DynamoDB Access Patterns (Queue entry)
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to join the matchmaking queue after connecting
SO THAT I am paired with an opponent and a game session starts automatically

### SCENARIO 1: Two players match successfully

**Scenario ID**: MATCH-STORY-001-S1

**GIVEN**
* Player A is connected (has a valid `CONN#<connA>` record in DynamoDB)
* Player B is connected (has a valid `CONN#<connB>` record in DynamoDB)
* Player A has already sent `joinQueue` and is waiting

**WHEN**
* Player B sends `{"action": "joinQueue"}`

**THEN**
* Both queue entries are deleted from DynamoDB
* A new `GAME#<gameId> / STATE` item is written with the initial GameState (30 HP, 0 mana slots, shuffled decks)
* Player A receives `{"status": "matched", "gameState": {...}}`
* Player B receives `{"status": "matched", "gameState": {...}}`

### SCENARIO 2: First player to join receives waiting confirmation

**Scenario ID**: MATCH-STORY-001-S2

**GIVEN**
* No other player is in the queue

**WHEN**
* A connected player sends `{"action": "joinQueue"}`

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written to DynamoDB
* The player receives `{"status": "waiting"}`
* No game is created

---

## Frontend Sub-Stories

### MATCH-FE-001.1: Matchmaking UI — queue entry and match notification

AS A player
I WANT the UI to show a "searching for opponent" state and transition to the game board when a match is found
SO THAT I know the system is working and can start playing immediately

#### SCENARIO 1: UI shows waiting state after joining queue

**Scenario ID**: MATCH-FE-001.1-S1

**GIVEN**
* The player is connected and on the lobby screen

**WHEN**
* The player clicks "Find Match"

**THEN**
* The client sends `{"action": "joinQueue"}` over the WebSocket
* The UI displays a "Searching for opponent…" indicator

#### SCENARIO 2: UI transitions to game board on match

**Scenario ID**: MATCH-FE-001.1-S2

**GIVEN**
* The player is in the waiting state

**WHEN**
* A `{"status": "matched", "gameState": {...}}` message arrives over the WebSocket

**THEN**
* The waiting indicator is hidden
* The game board is rendered with the initial game state (both players' HP, mana, hand)

---

## Backend Sub-Stories

### MATCH-BE-001.1: MatchmakingFunction pairs players and creates initial GameState

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 4.3 — Bounded Context: Matchmaking

AS A system
I WANT the MatchmakingFunction to atomically claim a waiting player from the queue, create an initial GameState, and notify both players
SO THAT exactly one game is created per pair with no duplicate matches

#### SCENARIO 1: Match created when opponent is waiting

**Scenario ID**: MATCH-BE-001.1-S1

**GIVEN**
* A `QUEUE / PLAYER#<opponentId>` item exists in DynamoDB
* A `joinQueue` event arrives for a second player

**WHEN**
* MatchmakingFunction executes

**THEN**
* Both queue items are deleted via conditional DynamoDB deletes (race-safe per R-4)
* A `GAME#<gameId> / STATE` item is written with a valid initial GameState: each player has 30 HP, 0 mana slots, 0 mana, a 20-card deck, and an empty hand
* `postToConnection` is called for both players with `{"status": "matched", "gameState": {...}}`

#### SCENARIO 2: No match when queue is empty

**Scenario ID**: MATCH-BE-001.1-S2

**GIVEN**
* The queue is empty

**WHEN**
* MatchmakingFunction handles a `joinQueue` event

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written
* `postToConnection` is called for the joining player with `{"status": "waiting"}`
* No game item is written

#### SCENARIO 3: Concurrent join race — only one match created

**Scenario ID**: MATCH-BE-001.1-S3

**GIVEN**
* Two `joinQueue` events for different players arrive simultaneously
* Both invocations attempt to claim the same waiting queue entry

**WHEN**
* Both MatchmakingFunction instances execute concurrently

**THEN**
* Exactly one invocation succeeds in deleting the queue entry (conditional delete)
* Exactly one game is created
* The losing invocation writes its own queue entry and returns `{"status": "waiting"}`

---

## Infrastructure Sub-Stories

### MATCH-INFRA-001.1: Deploy MatchmakingFunction Lambda

**Architecture Reference**: Section 7.2 — Infrastructure as Code (MatchmakingFunction)

AS A DevOps engineer
I WANT the MatchmakingFunction Lambda deployed via SAM
SO THAT the `joinQueue` WebSocket route has a compute target

#### SCENARIO 1: Lambda is deployed and invocable

**Scenario ID**: MATCH-INFRA-001.1-S1

**GIVEN**
* `template.yaml` defines `MatchmakingFunction` with `Runtime: python3.12` and the `joinQueue` route integration

**WHEN**
* `sam deploy` completes

**THEN**
* The Lambda exists in the AWS account
* A synthetic `joinQueue` invocation returns without a 5xx error
* The function's log group exists in CloudWatch

---

### MATCH-INFRA-001.2: DynamoDB queue and game access patterns

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Queue entry, Game)

AS A DevOps engineer
I WANT the DynamoDB table to support queue and game item access patterns
SO THAT matchmaking reads and writes succeed with correct key structure

#### SCENARIO 1: Queue item can be written and conditionally deleted

**Scenario ID**: MATCH-INFRA-001.2-S1

**GIVEN**
* The `GameTable` is deployed with `PK` (HASH) and `SK` (RANGE)

**WHEN**
* A `PutItem` with `PK=QUEUE, SK=PLAYER#<id>` is issued followed by a conditional `DeleteItem`

**THEN**
* Both operations succeed
* A second conditional `DeleteItem` on the same key fails with `ConditionalCheckFailedException`

#### SCENARIO 2: Game state item can be written and retrieved

**Scenario ID**: MATCH-INFRA-001.2-S2

**GIVEN**
* The `GameTable` is deployed

**WHEN**
* A `PutItem` with `PK=GAME#<gameId>, SK=STATE` is issued and then a `GetItem` is performed

**THEN**
* The retrieved item matches the written item

---

### MATCH-INFRA-001.3: Wire `joinQueue` route on WebSocket API Gateway

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code (WebSocketApi)

AS A DevOps engineer
I WANT the `joinQueue` WebSocket route integrated with MatchmakingFunction
SO THAT player queue requests trigger the matchmaking Lambda

#### SCENARIO 1: `joinQueue` route delivers event to Lambda

**Scenario ID**: MATCH-INFRA-001.3-S1

**GIVEN**
* `template.yaml` defines a `joinQueue` route on `WebSocketApi` pointing to `MatchmakingFunction`
* The stack is deployed

**WHEN**
* A connected client sends `{"action": "joinQueue"}`

**THEN**
* API Gateway invokes `MatchmakingFunction` with the correct event payload containing `connectionId` and `body`

---

### MATCH-INFRA-001.4: CloudWatch alarm and structured logging for MatchmakingFunction

**Architecture Reference**: Section 8.3 — Logging & Observability; Section 10.1 — Quality Tree (Operability)

AS A DevOps engineer
I WANT MatchmakingFunction to emit structured logs and have a CloudWatch error alarm
SO THAT matchmaking failures are observable and alertable

#### SCENARIO 1: Structured log emitted on match creation

**Scenario ID**: MATCH-INFRA-001.4-S1

**GIVEN**
* MatchmakingFunction uses AWS Lambda Powertools `Logger`
* A match is successfully created

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry appears in `/aws/lambda/MatchmakingFunction` containing `gameId`, `player1Id`, `player2Id`, and `durationMs`

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors

**Scenario ID**: MATCH-INFRA-001.4-S2

**GIVEN**
* A CloudWatch alarm is defined on the `Errors` metric for `MatchmakingFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* MatchmakingFunction throws an unhandled exception

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds

---

## Implementation Order

```
MATCH-INFRA-001.2 (DynamoDB queue + game patterns — table already exists from CONN-STORY-001)
  → MATCH-INFRA-001.1 (Lambda deploy)
  → MATCH-INFRA-001.3 (joinQueue route)
  → MATCH-INFRA-001.4 (monitoring)
  → MATCH-BE-001.1 (MatchmakingFunction logic)
  → MATCH-FE-001.1 (lobby UI + match transition)
  → MATCH-STORY-001 (E2E: two clients connect, join queue, verify game created and both notified)
```
