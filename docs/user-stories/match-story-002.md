# MATCH-STORY-002: Player Waits in Queue with No Opponent

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking, waiting branch); Section 5.1 — Building Block View (MatchmakingFunction); Section 5.3 — DynamoDB Access Patterns (Queue entry)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT to receive a "waiting" confirmation when I join the queue and no opponent is available
SO THAT I know my request was received and the system is looking for a match

### SCENARIO 1: Player receives waiting status when queue is empty

**Scenario ID**: MATCH-STORY-002-S1

**GIVEN**
* No other player is in the matchmaking queue
* A connected player sends `{"action": "joinQueue"}`

**WHEN**
* MatchmakingFunction processes the request

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written to DynamoDB
* The player receives `{"status": "waiting"}`
* No game is created

### SCENARIO 2: Player cannot join queue twice

**Scenario ID**: MATCH-STORY-002-S2

**GIVEN**
* A `QUEUE / PLAYER#<playerId>` item already exists for this player

**WHEN**
* The same player sends `{"action": "joinQueue"}` again

**THEN**
* No duplicate queue entry is written
* The player receives `{"status": "waiting"}` (idempotent response)

---

## Frontend Sub-Stories

### MATCH-FE-002.1: Lobby shows persistent waiting state

AS A player
I WANT the lobby to show a "Searching for opponent…" indicator that persists until a match is found
SO THAT I know the system is still looking and I haven't been dropped from the queue

#### SCENARIO 1: Waiting indicator persists after joining queue

**Scenario ID**: MATCH-FE-002.1-S1

**GIVEN**
* The player clicked "Find Match" and received `{"status": "waiting"}`

**WHEN**
* Time passes without a match

**THEN**
* The "Searching for opponent…" indicator remains visible
* The "Find Match" button is disabled to prevent duplicate queue entries

#### SCENARIO 2: Waiting indicator clears when match is found

**Scenario ID**: MATCH-FE-002.1-S2

**GIVEN**
* The player is in the waiting state

**WHEN**
* A `{"status": "matched", "gameState": {...}}` message arrives

**THEN**
* The waiting indicator is replaced by the game board

---

## Backend Sub-Stories

### MATCH-BE-002.1: MatchmakingFunction writes queue entry and responds with waiting status

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 5.3 — DynamoDB Access Patterns (Queue entry)

AS A system
I WANT MatchmakingFunction to write a queue entry and return `{"status": "waiting"}` when no opponent is available
SO THAT the player is registered for matching and informed of their status

#### SCENARIO 1: Queue entry written and waiting response sent

**Scenario ID**: MATCH-BE-002.1-S1

**GIVEN**
* No `QUEUE / PLAYER#*` items exist in DynamoDB
* A `joinQueue` event arrives

**WHEN**
* MatchmakingFunction executes

**THEN**
* A `PutItem` with `PK=QUEUE, SK=PLAYER#<playerId>` and `connectionId` is written
* `postToConnection` is called for the joining player with `{"status": "waiting"}`
* No game item is written

#### SCENARIO 2: Idempotent re-join — no duplicate entry

**Scenario ID**: MATCH-BE-002.1-S2

**GIVEN**
* A `QUEUE / PLAYER#<playerId>` item already exists

**WHEN**
* The same player sends `joinQueue` again

**THEN**
* A `PutItem` with `ConditionExpression: attribute_not_exists(PK)` either skips or overwrites idempotently
* The player receives `{"status": "waiting"}`
* No game is created

---

## Infrastructure Sub-Stories

### MATCH-INFRA-002.1: Compute — waiting path handled within MatchmakingFunction (no new Lambda)

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT to confirm that the waiting-queue path runs inside the existing MatchmakingFunction
SO THAT no additional compute resource is needed

#### SCENARIO 1: Waiting response sent within existing Lambda invocation

**Scenario ID**: MATCH-INFRA-002.1-S1

**GIVEN**
* MatchmakingFunction is deployed (MATCH-STORY-001)

**WHEN**
* A `joinQueue` event is processed with no opponent in the queue

**THEN**
* The queue write and waiting response occur within the same Lambda invocation

---

### MATCH-INFRA-002.2: DynamoDB — queue entry written and readable

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Queue entry)

AS A DevOps engineer
I WANT the queue entry to be written to DynamoDB and retrievable by MatchmakingFunction
SO THAT a subsequent player joining the queue can find and claim the waiting entry

#### SCENARIO 1: Queue item exists after player joins with no opponent

**Scenario ID**: MATCH-INFRA-002.2-S1

**GIVEN**
* No queue items exist

**WHEN**
* MatchmakingFunction processes a `joinQueue` event

**THEN**
* A `GetItem` on `PK=QUEUE, SK=PLAYER#<playerId>` returns the written item with `connectionId`

---

### MATCH-INFRA-002.3: WebSocket — waiting status delivered to joining player

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (waiting branch)

AS A DevOps engineer
I WANT the `{"status": "waiting"}` message delivered to the joining player's WebSocket connection
SO THAT the client can display the waiting state

#### SCENARIO 1: Waiting message delivered to joining player

**Scenario ID**: MATCH-INFRA-002.3-S1

**GIVEN**
* The joining player has an active WebSocket connection
* No opponent is in the queue

**WHEN**
* MatchmakingFunction calls `postToConnection` for the joining player

**THEN**
* The player's client receives `{"status": "waiting"}` within 500 ms

---

### MATCH-INFRA-002.4: CloudWatch — queue entry events logged

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT queue entry events to appear in structured logs
SO THAT queue depth and wait times are observable

#### SCENARIO 1: Structured log emitted when player enters queue

**Scenario ID**: MATCH-INFRA-002.4-S1

**GIVEN**
* MatchmakingFunction uses AWS Lambda Powertools `Logger`
* A player joins the queue with no opponent available

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry in `/aws/lambda/MatchmakingFunction` contains `playerId`, `event: "queue_entry"`, and `durationMs`

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors

**Scenario ID**: MATCH-INFRA-002.4-S2

**GIVEN**
* A CloudWatch alarm is defined on the `Errors` metric for `MatchmakingFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* MatchmakingFunction throws an unhandled exception during queue processing

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds

---

## Implementation Order

```
MATCH-INFRA-002.1 (confirm no new Lambda — reuses MatchmakingFunction)
  → MATCH-INFRA-002.2 (DynamoDB queue entry)
  → MATCH-INFRA-002.3 (WebSocket waiting delivery)
  → MATCH-INFRA-002.4 (logging)
  → MATCH-BE-002.1 (waiting path in MatchmakingFunction)
  → MATCH-FE-002.1 (persistent waiting indicator)
  → MATCH-STORY-002 (E2E: join queue alone → receive waiting status, DynamoDB entry exists)
```
