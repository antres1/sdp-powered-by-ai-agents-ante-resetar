# GAME-STORY-005: Bleeding Out Deals 1 Damage on Empty Deck Draw

**Architecture Reference**: Section 1.1 — Game Rules (Bleeding Out); Section 5.2 — Game Rules (pure functions); Section 6 — Runtime View, Scenario 3 (End Turn, Bleeding Out branch)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT the game to deal 1 damage to a player who draws from an empty deck
SO THAT the Bleeding Out rule is enforced and games cannot stall indefinitely

### SCENARIO 1: Bleeding Out reduces HP by 1 when deck is empty

**Scenario ID**: GAME-STORY-005-S1

**GIVEN**
* It is the player's turn
* The opponent's deck is empty

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* The opponent's HP is reduced by 1
* No card is added to the opponent's hand
* Both players receive `{"gameState": {...}}` with the updated state

### SCENARIO 2: Bleeding Out can trigger win condition

**Scenario ID**: GAME-STORY-005-S2

**GIVEN**
* The opponent has 1 HP remaining and an empty deck

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* The opponent's HP drops to 0
* Both players receive `{"status": "game_over", "winner": "<activePlayerId>"}`

---

## Frontend Sub-Stories

### GAME-FE-005.1: Display Bleeding Out event to both players

AS A player
I WANT to see a visual indicator when Bleeding Out occurs
SO THAT I understand why HP changed without a card being played

#### SCENARIO 1: Bleeding Out indicator shown when HP decreases without card play

**Scenario ID**: GAME-FE-005.1-S1

**GIVEN**
* A `gameState` update is received after an `endTurn`
* The drawing player's HP decreased and their hand size did not increase

**WHEN**
* The UI renders the updated state

**THEN**
* A "Bleeding Out!" label or animation is shown next to the affected player's HP
* The HP counter updates to the new value

---

## Backend Sub-Stories

### GAME-BE-005.1: `end_turn()` applies Bleeding Out when deck is empty

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 1.1 — Bleeding Out rule

AS A developer
I WANT `end_turn(state)` to reduce the drawing player's HP by 1 instead of drawing a card when their deck is empty
SO THAT the Bleeding Out rule is unit-testable without infrastructure

#### SCENARIO 1: HP reduced by 1 when deck is empty

**Scenario ID**: GAME-BE-005.1-S1

**GIVEN**
* A `GameState` where the opponent's deck is empty and HP is 5

**WHEN**
* `end_turn(state)` is called

**THEN**
* Returned state has opponent HP = 4
* Opponent hand size is unchanged
* Active player switches to the opponent

#### SCENARIO 2: Bleeding Out with 1 HP results in HP = 0

**Scenario ID**: GAME-BE-005.1-S2

**GIVEN**
* A `GameState` where the opponent's deck is empty and HP is 1

**WHEN**
* `end_turn(state)` is called

**THEN**
* Returned state has opponent HP = 0
* `is_game_over(state)` returns the active player's ID as winner

#### SCENARIO 3: Normal draw takes priority when deck is non-empty

**Scenario ID**: GAME-BE-005.1-S3

**GIVEN**
* A `GameState` where the opponent's deck has cards

**WHEN**
* `end_turn(state)` is called

**THEN**
* No HP damage is applied
* One card is moved from deck to hand

---

## Infrastructure Sub-Stories

### GAME-INFRA-005.1: Compute — Bleeding Out handled within EndTurnFunction (no new Lambda)

**Architecture Reference**: Section 5.1 — EndTurnFunction; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT to confirm that Bleeding Out logic runs inside the existing EndTurnFunction
SO THAT no additional compute resource is needed

#### SCENARIO 1: Bleeding Out damage applied within existing Lambda invocation

**Scenario ID**: GAME-INFRA-005.1-S1

**GIVEN**
* EndTurnFunction is deployed (GAME-STORY-002)

**WHEN**
* An end-turn action is processed with an empty opponent deck

**THEN**
* The HP reduction and state persistence occur within the same Lambda invocation

---

### GAME-INFRA-005.2: DynamoDB — Bleeding Out state persisted correctly

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Game); Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT the post-Bleeding-Out game state to be written to DynamoDB with the correct HP value
SO THAT the damage is durable

#### SCENARIO 1: DynamoDB item reflects HP reduction after Bleeding Out

**Scenario ID**: GAME-INFRA-005.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists with opponent HP = 5 and empty deck

**WHEN**
* EndTurnFunction processes the end-turn action

**THEN**
* A `GetItem` on `GAME#<gameId> / STATE` returns state with opponent HP = 4

---

### GAME-INFRA-005.3: WebSocket — updated state broadcast to both players after Bleeding Out

**Architecture Reference**: Section 6 — Runtime View, Scenario 3; Section 8.5 — WebSocket Connection Lifecycle

AS A DevOps engineer
I WANT the post-Bleeding-Out game state delivered to both players via WebSocket
SO THAT both clients reflect the HP change in real time

#### SCENARIO 1: Both players receive updated state after Bleeding Out

**Scenario ID**: GAME-INFRA-005.3-S1

**GIVEN**
* Both players have active WebSocket connections
* An end-turn with Bleeding Out is processed

**WHEN**
* EndTurnFunction calls `postToConnection` for both players

**THEN**
* Both clients receive `{"gameState": {...}}` with the reduced HP within 500 ms (p95)

---

### GAME-INFRA-005.4: CloudWatch — Bleeding Out events logged

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT Bleeding Out events to appear in structured logs
SO THAT they are auditable and distinguishable from normal draws

#### SCENARIO 1: Structured log entry emitted on Bleeding Out

**Scenario ID**: GAME-INFRA-005.4-S1

**GIVEN**
* EndTurnFunction uses AWS Lambda Powertools `Logger`
* A Bleeding Out event occurs

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry in `/aws/lambda/EndTurnFunction` contains `gameId`, `playerId`, `event: "bleeding_out"`, `hpAfter`, and `durationMs`

---

## Implementation Order

```
GAME-INFRA-005.1 (confirm no new Lambda — reuses EndTurnFunction)
  → GAME-INFRA-005.2 (DynamoDB HP persistence)
  → GAME-INFRA-005.3 (WebSocket broadcast)
  → GAME-INFRA-005.4 (logging)
  → GAME-BE-005.1 (Bleeding Out in end_turn() pure function)
  → GAME-FE-005.1 (Bleeding Out UI indicator)
  → GAME-STORY-005 (E2E: end turn with empty deck → opponent HP reduced, both players notified)
```
