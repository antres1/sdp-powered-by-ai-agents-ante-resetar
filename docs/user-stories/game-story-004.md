# GAME-STORY-004: Rule Violation — Insufficient Mana Rejected

**Architecture Reference**: Section 8.2 — Error Handling; Section 5.2 — Game Rules (pure functions); Section 6 — Runtime View, Scenario 2 (Play Card, rule violation branch)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT the server to reject a card play when I don't have enough mana
SO THAT the game rules are enforced and only the acting player sees the error

### SCENARIO 1: Insufficient mana returns error to acting player only

**Scenario ID**: GAME-STORY-004-S1

**GIVEN**
* It is the player's turn
* The player has 2 mana available
* The player attempts to play a card with cost 5

**WHEN**
* The player sends `{"action": "playCard", "cardIndex": 0}`

**THEN**
* The game state is unchanged (no DynamoDB write)
* Only the acting player receives `{"error": "not enough mana"}`
* The opponent receives nothing

### SCENARIO 2: Invalid card index returns error to acting player only

**Scenario ID**: GAME-STORY-004-S2

**GIVEN**
* It is the player's turn
* The player's hand contains 2 cards (indices 0 and 1)

**WHEN**
* The player sends `{"action": "playCard", "cardIndex": 5}`

**THEN**
* The game state is unchanged
* Only the acting player receives `{"error": "invalid card index"}`

---

## Frontend Sub-Stories

### GAME-FE-004.1: Display rule violation error inline

AS A player
I WANT to see an inline error message when my card play is rejected
SO THAT I understand why the action failed without losing my game state

#### SCENARIO 1: Error toast shown on rule violation response

**Scenario ID**: GAME-FE-004.1-S1

**GIVEN**
* The player sends a `playCard` action

**WHEN**
* The server responds with `{"error": "not enough mana"}`

**THEN**
* A non-blocking error toast displays "Not enough mana"
* The card remains in the player's hand (UI state unchanged)
* The toast auto-dismisses after 3 seconds

#### SCENARIO 2: Cards re-enabled after rejected play

**Scenario ID**: GAME-FE-004.1-S2

**GIVEN**
* The player clicked a card (temporarily disabling it to prevent double-send)

**WHEN**
* An `{"error": ...}` response arrives

**THEN**
* The card is re-enabled in the UI

---

## Backend Sub-Stories

### GAME-BE-004.1: `play_card()` raises RuleViolation on insufficient mana

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 8.2 — Error Handling

AS A developer
I WANT `play_card(state, card_index)` to raise a `RuleViolation` when mana is insufficient or the card index is invalid
SO THAT rule enforcement is unit-testable without infrastructure

#### SCENARIO 1: RuleViolation raised when mana < card cost

**Scenario ID**: GAME-BE-004.1-S1

**GIVEN**
* A `GameState` where the active player has `mana=2` and hand `[5, 3]`

**WHEN**
* `play_card(state, card_index=0)` is called (card cost = 5)

**THEN**
* `RuleViolation("not enough mana")` is raised
* The input state is unchanged

#### SCENARIO 2: RuleViolation raised on invalid card index

**Scenario ID**: GAME-BE-004.1-S2

**GIVEN**
* A `GameState` where the active player's hand has 2 cards

**WHEN**
* `play_card(state, card_index=5)` is called

**THEN**
* `RuleViolation("invalid card index")` is raised

### GAME-BE-004.2: PlayCardFunction handler catches RuleViolation and sends error to acting player only

**Architecture Reference**: Section 8.2 — Error Handling; Section 5.2 — Lambda Handler (adapter/in)

AS A system
I WANT PlayCardFunction to catch `RuleViolation` and send the error message only to the acting player
SO THAT the opponent is not notified of failed actions and game state is not corrupted

#### SCENARIO 1: RuleViolation caught — error sent to acting player, no state write

**Scenario ID**: GAME-BE-004.2-S1

**GIVEN**
* `play_card()` raises `RuleViolation("not enough mana")`

**WHEN**
* The handler catches the exception

**THEN**
* `GameRepository.save_game()` is NOT called
* `PlayerNotifier.post_to_connection()` is called exactly once, for the acting player's `connectionId`, with `{"error": "not enough mana"}`
* The opponent's connection receives nothing

---

## Infrastructure Sub-Stories

### GAME-INFRA-004.1: Compute — rule violation handled within PlayCardFunction (no new Lambda)

**Architecture Reference**: Section 5.1 — PlayCardFunction; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT to confirm that rule violation handling runs inside the existing PlayCardFunction
SO THAT no additional compute resource is needed

#### SCENARIO 1: Rule violation response sent within existing Lambda invocation

**Scenario ID**: GAME-INFRA-004.1-S1

**GIVEN**
* PlayCardFunction is deployed (GAME-STORY-001)

**WHEN**
* A card play with insufficient mana is processed

**THEN**
* The error response is sent within the same Lambda invocation
* The Lambda returns HTTP 200 (WebSocket frame delivered; error is in the payload)

---

### GAME-INFRA-004.2: DynamoDB — no write on rule violation

**Architecture Reference**: Section 8.4 — Game State Consistency; Section 5.3 — DynamoDB Access Patterns (Game)

AS A DevOps engineer
I WANT to verify that a rule violation does not result in a DynamoDB write
SO THAT game state integrity is preserved on rejected actions

#### SCENARIO 1: DynamoDB item unchanged after rule violation

**Scenario ID**: GAME-INFRA-004.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists with a known state
* A card play with insufficient mana is processed

**WHEN**
* PlayCardFunction completes

**THEN**
* A `GetItem` on `GAME#<gameId> / STATE` returns the original unchanged state

---

### GAME-INFRA-004.3: WebSocket — error delivered only to acting player

**Architecture Reference**: Section 8.2 — Error Handling; Section 6 — Runtime View, Scenario 2 (rule violation branch)

AS A DevOps engineer
I WANT to verify that the error message is delivered only to the acting player's WebSocket connection
SO THAT the opponent's client is not affected by the other player's rule violations

#### SCENARIO 1: Only acting player's connection receives error frame

**Scenario ID**: GAME-INFRA-004.3-S1

**GIVEN**
* Both players have active WebSocket connections
* A rule violation occurs for player A

**WHEN**
* PlayCardFunction calls `postToConnection`

**THEN**
* `postToConnection` is called exactly once with player A's `connectionId`
* Player B's connection receives no frame for this action

---

### GAME-INFRA-004.4: CloudWatch — rule violations logged as warnings

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT rule violations to appear as structured warning logs in CloudWatch
SO THAT patterns of invalid actions are observable (e.g. client bugs sending unaffordable plays)

#### SCENARIO 1: Structured warning log emitted on rule violation

**Scenario ID**: GAME-INFRA-004.4-S1

**GIVEN**
* PlayCardFunction uses AWS Lambda Powertools `Logger`
* A `RuleViolation` is caught

**WHEN**
* The handler completes

**THEN**
* A JSON log entry at `WARNING` level appears in `/aws/lambda/PlayCardFunction` containing `gameId`, `playerId`, `violation`, and `durationMs`

---

## Implementation Order

```
GAME-INFRA-004.1 (confirm no new Lambda — reuses PlayCardFunction)
  → GAME-INFRA-004.2 (verify no DynamoDB write on violation)
  → GAME-INFRA-004.3 (WebSocket error delivery to acting player only)
  → GAME-INFRA-004.4 (warning logging)
  → GAME-BE-004.1 (RuleViolation in play_card() pure function)
  → GAME-BE-004.2 (handler catches RuleViolation, sends error to acting player only)
  → GAME-FE-004.1 (error toast + card re-enable)
  → GAME-STORY-004 (E2E: play unaffordable card → only acting player sees error, state unchanged)
```
