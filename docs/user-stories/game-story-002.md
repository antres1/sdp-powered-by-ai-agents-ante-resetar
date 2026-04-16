# GAME-STORY-002: Player Ends Their Turn

**Architecture Reference**: Section 6 — Runtime View, Scenario 3 (End Turn); Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 1.1 — Game Rules (Bleeding Out, Overload, mana slots)
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to end my turn
SO THAT the opponent's mana is refilled, they draw a card, and control passes to them

### SCENARIO 1: Normal end turn — opponent draws a card and becomes active

**Scenario ID**: GAME-STORY-002-S1

**GIVEN**
* It is the player's turn
* The opponent has a non-empty deck and fewer than 5 cards in hand
* The opponent has N mana slots (N < 10)

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* Opponent mana slots increment to N+1 (capped at 10)
* Opponent mana is refilled to N+1
* One card is moved from the opponent's deck to their hand
* The active player switches to the opponent
* Both players receive `{"gameState": {...}}` with the updated state

### SCENARIO 2: Bleeding Out — opponent draws from empty deck and takes 1 damage

**Scenario ID**: GAME-STORY-002-S2

**GIVEN**
* It is the player's turn
* The opponent's deck is empty

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* Opponent mana slots and mana are still incremented/refilled
* Opponent HP is reduced by 1 (Bleeding Out)
* No card is added to the opponent's hand
* Both players receive the updated game state

### SCENARIO 3: Overload — drawn card discarded when opponent's hand is full

**Scenario ID**: GAME-STORY-002-S3

**GIVEN**
* It is the player's turn
* The opponent's hand already contains 5 cards and the deck is non-empty

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* The top card of the opponent's deck is removed (discarded)
* The opponent's hand size remains 5
* Both players receive the updated game state

### SCENARIO 4: End turn rejected when it is not the player's turn

**Scenario ID**: GAME-STORY-002-S4

**GIVEN**
* It is the opponent's turn

**WHEN**
* The inactive player sends `{"action": "endTurn"}`

**THEN**
* Game state is unchanged
* Only the acting player receives `{"error": "not your turn"}`

---

## Frontend Sub-Stories

### GAME-FE-002.1: End Turn button and turn indicator

AS A player
I WANT an "End Turn" button that is only active on my turn and shows whose turn it is
SO THAT I know when I can act and can pass control to my opponent

#### SCENARIO 1: End Turn button enabled only on active player's turn

**Scenario ID**: GAME-FE-002.1-S1

**GIVEN**
* A `gameState` message is received

**WHEN**
* The UI renders

**THEN**
* The "End Turn" button is enabled if `gameState.activePlayerId === myPlayerId`
* The "End Turn" button is disabled otherwise
* A turn indicator shows "Your turn" or "Opponent's turn"

#### SCENARIO 2: Clicking End Turn sends endTurn action

**Scenario ID**: GAME-FE-002.1-S2

**GIVEN**
* It is the player's turn and the End Turn button is enabled

**WHEN**
* The player clicks "End Turn"

**THEN**
* The client sends `{"action": "endTurn"}` over the WebSocket
* The button is immediately disabled to prevent double-send

---

## Backend Sub-Stories

### GAME-BE-002.1: EndTurnFunction orchestrates turn transition

**Architecture Reference**: Section 5.2 — Game Use Case; Section 8.4 — Game State Consistency

AS A system
I WANT EndTurnFunction to load game state, call `end_turn()`, persist the result, and notify both players
SO THAT turn transitions are atomic and immediately visible to both players

#### SCENARIO 1: Valid end turn — state persisted and both players notified

**Scenario ID**: GAME-BE-002.1-S1

**GIVEN**
* The `connectionId` maps to the active player
* `GameRepository.get_game()` returns a valid `GameState`

**WHEN**
* EndTurnFunction is invoked

**THEN**
* `end_turn(state)` is called and returns a new `GameState`
* `GameRepository.save_game()` is called with the new state
* `PlayerNotifier.post_to_connection()` is called for both players

#### SCENARIO 2: Not active player — rejected before domain call

**Scenario ID**: GAME-BE-002.1-S2

**GIVEN**
* The `connectionId` maps to the inactive player

**WHEN**
* EndTurnFunction is invoked

**THEN**
* `end_turn()` is never called
* Only the acting player receives `{"error": "not your turn"}`
* No DynamoDB write occurs

### GAME-BE-002.2: `end_turn()` pure domain function

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A developer
I WANT a pure `end_turn(state)` function covering all turn-transition rules
SO THAT Bleeding Out, Overload, mana slot increment, and active player switch are unit-testable without infrastructure

#### SCENARIO 1: Normal draw — card moved to hand, mana refilled, player switched

**Scenario ID**: GAME-BE-002.2-S1

**GIVEN**
* A `GameState` where the opponent has a non-empty deck, hand size < 5, and mana slots = 3

**WHEN**
* `end_turn(state)` is called

**THEN**
* Opponent mana slots = 4, mana = 4
* Opponent hand gains one card from the top of the deck
* Active player switches to the opponent
* Input state is unchanged (immutability)

#### SCENARIO 2: Bleeding Out — empty deck deals 1 damage

**Scenario ID**: GAME-BE-002.2-S2

**GIVEN**
* The opponent's deck is empty

**WHEN**
* `end_turn(state)` is called

**THEN**
* Opponent HP is reduced by 1
* Opponent hand size is unchanged
* Active player switches

#### SCENARIO 3: Overload — full hand discards drawn card

**Scenario ID**: GAME-BE-002.2-S3

**GIVEN**
* The opponent's hand has 5 cards and deck is non-empty

**WHEN**
* `end_turn(state)` is called

**THEN**
* The top card is removed from the deck
* Opponent hand size remains 5
* Active player switches

#### SCENARIO 4: Mana slots capped at 10

**Scenario ID**: GAME-BE-002.2-S4

**GIVEN**
* The opponent already has 10 mana slots

**WHEN**
* `end_turn(state)` is called

**THEN**
* Mana slots remain 10 (no increment beyond cap)
* Mana is refilled to 10

---

## Infrastructure Sub-Stories

### GAME-INFRA-002.1: Deploy EndTurnFunction Lambda

**Architecture Reference**: Section 7.2 — Infrastructure as Code (EndTurnFunction)

AS A DevOps engineer
I WANT EndTurnFunction deployed via SAM with the `endTurn` route integration
SO THAT end-turn WebSocket frames have a compute target

#### SCENARIO 1: Lambda deployed and invocable

**Scenario ID**: GAME-INFRA-002.1-S1

**GIVEN**
* `template.yaml` defines `EndTurnFunction` with `Runtime: python3.12` and the `endTurn` route

**WHEN**
* `sam deploy` completes

**THEN**
* The Lambda exists and a synthetic invocation returns without a 5xx error
* The log group `/aws/lambda/EndTurnFunction` exists

---

### GAME-INFRA-002.2: DynamoDB read/write access for EndTurnFunction

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Game); Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT EndTurnFunction's IAM role to allow `GetItem` and `PutItem` on `GameTable`
SO THAT the Lambda can load and persist game state after each turn

#### SCENARIO 1: GetItem and conditional PutItem succeed for EndTurnFunction

**Scenario ID**: GAME-INFRA-002.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists in `GameTable`
* EndTurnFunction's execution role has `dynamodb:GetItem` and `dynamodb:PutItem` on `GameTable`

**WHEN**
* EndTurnFunction performs a `GetItem` followed by a conditional `PutItem`

**THEN**
* Both operations succeed without an `AccessDeniedException`

---

### GAME-INFRA-002.3: Wire `endTurn` route on WebSocket API Gateway

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the `endTurn` WebSocket route integrated with EndTurnFunction
SO THAT end-turn frames are routed to the correct Lambda

#### SCENARIO 1: `endTurn` route delivers event to Lambda

**Scenario ID**: GAME-INFRA-002.3-S1

**GIVEN**
* `template.yaml` defines an `endTurn` route pointing to `EndTurnFunction`
* The stack is deployed

**WHEN**
* A connected client sends `{"action": "endTurn"}`

**THEN**
* API Gateway invokes `EndTurnFunction` with `connectionId` and the message body

---

### GAME-INFRA-002.4: CloudWatch alarm and structured logging for EndTurnFunction

**Architecture Reference**: Section 8.3 — Logging & Observability; Section 10.2 — Responsiveness (≤ 300 ms p95)

AS A DevOps engineer
I WANT EndTurnFunction to emit structured logs and have a CloudWatch error alarm
SO THAT turn-transition failures are observable and latency is trackable

#### SCENARIO 1: Structured log emitted on every invocation

**Scenario ID**: GAME-INFRA-002.4-S1

**GIVEN**
* EndTurnFunction uses AWS Lambda Powertools `Logger` and `Tracer`

**WHEN**
* A turn transition is processed

**THEN**
* A JSON log entry appears in `/aws/lambda/EndTurnFunction` containing `gameId`, `playerId`, `action`, and `durationMs`
* An X-Ray trace links API Gateway → Lambda → DynamoDB

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors

**Scenario ID**: GAME-INFRA-002.4-S2

**GIVEN**
* A CloudWatch alarm is defined on `Errors` metric for `EndTurnFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* EndTurnFunction throws an unhandled exception

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds

---

## Implementation Order

```
GAME-INFRA-002.1 (Lambda deploy)
  → GAME-INFRA-002.2 (DynamoDB IAM)
  → GAME-INFRA-002.3 (endTurn route)
  → GAME-INFRA-002.4 (monitoring)
  → GAME-BE-002.2 (end_turn() pure domain function)
  → GAME-BE-002.1 (EndTurnFunction handler + use case)
  → GAME-FE-002.1 (End Turn button + turn indicator)
  → GAME-STORY-002 (E2E: end turn, verify mana/draw/switch and both players notified)
```
