# GAME-STORY-006: Overload Discards Card When Hand Is Full

**Architecture Reference**: Section 1.1 — Game Rules (Overload); Section 5.2 — Game Rules (pure functions); Section 6 — Runtime View, Scenario 3 (End Turn, Overload branch)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT the game to discard the drawn card when my hand is already full (5 cards)
SO THAT the Overload rule is enforced and hand size never exceeds 5

### SCENARIO 1: Drawn card discarded when hand is full

**Scenario ID**: GAME-STORY-006-S1

**GIVEN**
* It is the player's turn
* The opponent's hand contains exactly 5 cards
* The opponent's deck is non-empty

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* The top card of the opponent's deck is removed (discarded)
* The opponent's hand size remains 5
* Both players receive `{"gameState": {...}}` with the updated state

### SCENARIO 2: Normal draw when hand has fewer than 5 cards

**Scenario ID**: GAME-STORY-006-S2

**GIVEN**
* The opponent's hand contains 4 cards and the deck is non-empty

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* One card is moved from the deck to the opponent's hand
* The opponent's hand size becomes 5
* No card is discarded

---

## Frontend Sub-Stories

### GAME-FE-006.1: Display Overload event to both players

AS A player
I WANT to see a visual indicator when a card is discarded due to Overload
SO THAT I understand why the hand size did not increase

#### SCENARIO 1: Overload indicator shown when hand stays at 5

**Scenario ID**: GAME-FE-006.1-S1

**GIVEN**
* A `gameState` update is received after an `endTurn`
* The drawing player's hand size is still 5 and their deck shrank by 1

**WHEN**
* The UI renders the updated state

**THEN**
* An "Overload! Card discarded" label or animation is shown
* The hand display remains at 5 cards

---

## Backend Sub-Stories

### GAME-BE-006.1: `end_turn()` applies Overload when hand is full

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 1.1 — Overload rule

AS A developer
I WANT `end_turn(state)` to discard the drawn card instead of adding it to hand when hand size is 5
SO THAT the Overload rule is unit-testable without infrastructure

#### SCENARIO 1: Card discarded when hand size is 5

**Scenario ID**: GAME-BE-006.1-S1

**GIVEN**
* A `GameState` where the opponent's hand has 5 cards and deck has 3 cards

**WHEN**
* `end_turn(state)` is called

**THEN**
* Returned state has opponent hand size = 5 (unchanged)
* Opponent deck size = 2 (top card removed)
* Active player switches

#### SCENARIO 2: Card added to hand when hand size is less than 5

**Scenario ID**: GAME-BE-006.1-S2

**GIVEN**
* A `GameState` where the opponent's hand has 4 cards and deck has 3 cards

**WHEN**
* `end_turn(state)` is called

**THEN**
* Returned state has opponent hand size = 5
* Opponent deck size = 2

#### SCENARIO 3: Overload and Bleeding Out are mutually exclusive

**Scenario ID**: GAME-BE-006.1-S3

**GIVEN**
* A `GameState` where the opponent's deck is empty and hand has 5 cards

**WHEN**
* `end_turn(state)` is called

**THEN**
* Bleeding Out applies (HP reduced by 1)
* Overload does NOT apply (no card to discard)
* Hand size remains 5

---

## Infrastructure Sub-Stories

### GAME-INFRA-006.1: Compute — Overload handled within EndTurnFunction (no new Lambda)

**Architecture Reference**: Section 5.1 — EndTurnFunction; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT to confirm that Overload logic runs inside the existing EndTurnFunction
SO THAT no additional compute resource is needed

#### SCENARIO 1: Overload discard occurs within existing Lambda invocation

**Scenario ID**: GAME-INFRA-006.1-S1

**GIVEN**
* EndTurnFunction is deployed (GAME-STORY-002)

**WHEN**
* An end-turn action is processed with a full opponent hand

**THEN**
* The discard and state persistence occur within the same Lambda invocation

---

### GAME-INFRA-006.2: DynamoDB — Overload state persisted correctly

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Game); Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT the post-Overload game state written to DynamoDB with the correct hand and deck sizes
SO THAT the discard is durable

#### SCENARIO 1: DynamoDB item reflects discard after Overload

**Scenario ID**: GAME-INFRA-006.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists with opponent hand size = 5 and deck size = 3

**WHEN**
* EndTurnFunction processes the end-turn action

**THEN**
* A `GetItem` on `GAME#<gameId> / STATE` returns state with opponent hand size = 5 and deck size = 2

---

### GAME-INFRA-006.3: WebSocket — updated state broadcast to both players after Overload

**Architecture Reference**: Section 6 — Runtime View, Scenario 3; Section 8.5 — WebSocket Connection Lifecycle

AS A DevOps engineer
I WANT the post-Overload game state delivered to both players via WebSocket
SO THAT both clients reflect the discard in real time

#### SCENARIO 1: Both players receive updated state after Overload

**Scenario ID**: GAME-INFRA-006.3-S1

**GIVEN**
* Both players have active WebSocket connections
* An end-turn with Overload is processed

**WHEN**
* EndTurnFunction calls `postToConnection` for both players

**THEN**
* Both clients receive `{"gameState": {...}}` with hand size = 5 and reduced deck size within 500 ms (p95)

---

### GAME-INFRA-006.4: CloudWatch — Overload events logged

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT Overload events to appear in structured logs
SO THAT they are auditable and distinguishable from normal draws

#### SCENARIO 1: Structured log entry emitted on Overload

**Scenario ID**: GAME-INFRA-006.4-S1

**GIVEN**
* EndTurnFunction uses AWS Lambda Powertools `Logger`
* An Overload event occurs

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry in `/aws/lambda/EndTurnFunction` contains `gameId`, `playerId`, `event: "overload"`, `discardedCard`, and `durationMs`

---

## Implementation Order

```
GAME-INFRA-006.1 (confirm no new Lambda — reuses EndTurnFunction)
  → GAME-INFRA-006.2 (DynamoDB discard persistence)
  → GAME-INFRA-006.3 (WebSocket broadcast)
  → GAME-INFRA-006.4 (logging)
  → GAME-BE-006.1 (Overload in end_turn() pure function)
  → GAME-FE-006.1 (Overload UI indicator)
  → GAME-STORY-006 (E2E: end turn with full hand → card discarded, hand stays at 5, both players notified)
```
