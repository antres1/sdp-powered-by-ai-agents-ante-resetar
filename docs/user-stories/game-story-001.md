# GAME-STORY-001: Player Plays a Card

**Architecture Reference**: Section 6 — Runtime View, Scenario 2 (Play Card); Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 8.2 — Error Handling; Section 8.4 — Game State Consistency
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to play a card from my hand during my turn
SO THAT the card's mana cost is deducted, the opponent takes damage equal to the card's cost, and both players see the updated game state

### SCENARIO 1: Valid card play reduces mana and deals damage

**Scenario ID**: GAME-STORY-001-S1

**GIVEN**
* It is the player's turn
* The player has a card with cost 3 in their hand at index 2
* The player has at least 3 mana available

**WHEN**
* The player sends `{"action": "playCard", "cardIndex": 2}`

**THEN**
* The card is removed from the player's hand
* The player's mana is reduced by 3
* The opponent's health is reduced by 3
* Both players receive `{"gameState": {...}}` with the updated state

### SCENARIO 2: Card play rejected when mana is insufficient

**Scenario ID**: GAME-STORY-001-S2

**GIVEN**
* It is the player's turn
* The player has a card with cost 5 in their hand
* The player has only 2 mana available

**WHEN**
* The player sends `{"action": "playCard", "cardIndex": 0}`

**THEN**
* The game state is unchanged (no DynamoDB write)
* Only the acting player receives `{"error": "not enough mana"}`
* The opponent receives nothing

### SCENARIO 3: Card play rejected when it is not the player's turn

**Scenario ID**: GAME-STORY-001-S3

**GIVEN**
* It is the opponent's turn

**WHEN**
* The inactive player sends `{"action": "playCard", "cardIndex": 0}`

**THEN**
* The game state is unchanged
* Only the acting player receives `{"error": "not your turn"}`

---

## Frontend Sub-Stories

### GAME-FE-001.1: Game board renders hand and handles card play interaction

AS A player
I WANT to see my hand of cards and click a card to play it
SO THAT I can take actions during my turn

#### SCENARIO 1: Hand is rendered with playable cards highlighted

**Scenario ID**: GAME-FE-001.1-S1

**GIVEN**
* A `gameState` message has been received
* It is the player's turn
* The player has 3 mana and cards with costs [1, 4, 2] in hand

**WHEN**
* The game board renders

**THEN**
* All three cards are displayed
* Cards with cost ≤ 3 (costs 1 and 2) are visually enabled
* The card with cost 4 is visually disabled (unaffordable)

#### SCENARIO 2: Clicking a card sends playCard action

**Scenario ID**: GAME-FE-001.1-S2

**GIVEN**
* It is the player's turn and a card at index 1 is affordable

**WHEN**
* The player clicks that card

**THEN**
* The client sends `{"action": "playCard", "cardIndex": 1}` over the WebSocket
* The card is temporarily disabled to prevent double-send

#### SCENARIO 3: Error message displayed on rule violation

**Scenario ID**: GAME-FE-001.1-S3

**GIVEN**
* The player sends a card play action

**WHEN**
* The server responds with `{"error": "not enough mana"}`

**THEN**
* A toast or inline error message displays "Not enough mana"
* The card is re-enabled in the UI

---

## Backend Sub-Stories

### GAME-BE-001.1: PlayCardFunction applies card-play domain logic

**Architecture Reference**: Section 5.2 — Game Use Case, Game Rules, GameRepository, PlayerNotifier

AS A system
I WANT PlayCardFunction to load game state, delegate to the domain `play_card()` pure function, persist the result, and notify both players
SO THAT card plays are rule-enforced, atomic, and immediately visible to both players

#### SCENARIO 1: Valid play — state persisted and both players notified

**Scenario ID**: GAME-BE-001.1-S1

**GIVEN**
* `GameRepository.get_game()` returns a valid `GameState` where the acting player is active and has sufficient mana
* `cardIndex` points to a valid card in the hand

**WHEN**
* `play_card(state, cardIndex)` is called

**THEN**
* Returns a new `GameState` with: card removed from hand, mana reduced by card cost, opponent HP reduced by card cost
* `GameRepository.save_game()` is called with the new state
* `PlayerNotifier.post_to_connection()` is called for both players with the new state

#### SCENARIO 2: Insufficient mana — RuleViolation raised, no state mutation

**Scenario ID**: GAME-BE-001.1-S2

**GIVEN**
* The acting player has 2 mana and attempts to play a card costing 5

**WHEN**
* `play_card(state, cardIndex)` is called

**THEN**
* A `RuleViolation("not enough mana")` is raised
* `GameRepository.save_game()` is NOT called
* Only the acting player's connection receives `{"error": "not enough mana"}`

#### SCENARIO 3: Not active player — rejected before domain call

**Scenario ID**: GAME-BE-001.1-S3

**GIVEN**
* The `connectionId` maps to a player who is NOT the active player in the loaded `GameState`

**WHEN**
* PlayCardFunction is invoked

**THEN**
* The domain `play_card()` is never called
* Only the acting player receives `{"error": "not your turn"}`
* No DynamoDB write occurs

### GAME-BE-001.2: `play_card()` pure domain function

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A developer
I WANT a pure `play_card(state, card_index)` function with no AWS imports
SO THAT all rule logic is unit-testable without infrastructure

#### SCENARIO 1: Card removed, mana deducted, opponent damaged

**Scenario ID**: GAME-BE-001.2-S1

**GIVEN**
* A `GameState` where active player has `mana=4`, hand `[1, 3, 2]`

**WHEN**
* `play_card(state, card_index=1)` is called (card cost = 3)

**THEN**
* Returned state has active player `mana=1`, hand `[1, 2]`
* Opponent HP reduced by 3
* Input state is unchanged (immutability)

---

## Infrastructure Sub-Stories

### GAME-INFRA-001.1: Deploy PlayCardFunction Lambda

**Architecture Reference**: Section 7.2 — Infrastructure as Code (PlayCardFunction)

AS A DevOps engineer
I WANT PlayCardFunction deployed via SAM with the `playCard` route integration
SO THAT card-play WebSocket frames have a compute target

#### SCENARIO 1: Lambda deployed and invocable

**Scenario ID**: GAME-INFRA-001.1-S1

**GIVEN**
* `template.yaml` defines `PlayCardFunction` with `Runtime: python3.12` and the `playCard` route

**WHEN**
* `sam deploy` completes

**THEN**
* The Lambda exists and a synthetic invocation returns without a 5xx error
* The log group `/aws/lambda/PlayCardFunction` exists

---

### GAME-INFRA-001.2: DynamoDB game state read/write access for PlayCardFunction

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Game); Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT PlayCardFunction's IAM role to allow `GetItem` and `PutItem` on `GameTable`
SO THAT the Lambda can load and persist game state

#### SCENARIO 1: Conditional PutItem succeeds on existing game item

**Scenario ID**: GAME-INFRA-001.2-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists in `GameTable`

**WHEN**
* A conditional `PutItem` with `attribute_exists(PK)` is issued

**THEN**
* The write succeeds and the item is updated

#### SCENARIO 2: Conditional PutItem fails on missing game item

**Scenario ID**: GAME-INFRA-001.2-S2

**GIVEN**
* No item exists for `GAME#<unknownId> / STATE`

**WHEN**
* A conditional `PutItem` with `attribute_exists(PK)` is issued

**THEN**
* DynamoDB returns `ConditionalCheckFailedException`

---

### GAME-INFRA-001.3: Wire `playCard` route on WebSocket API Gateway

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the `playCard` WebSocket route integrated with PlayCardFunction
SO THAT card-play frames are routed to the correct Lambda

#### SCENARIO 1: `playCard` route delivers event to Lambda

**Scenario ID**: GAME-INFRA-001.3-S1

**GIVEN**
* `template.yaml` defines a `playCard` route pointing to `PlayCardFunction`
* The stack is deployed

**WHEN**
* A connected client sends `{"action": "playCard", "cardIndex": 0}`

**THEN**
* API Gateway invokes `PlayCardFunction` with `connectionId` and the message body

---

### GAME-INFRA-001.4: CloudWatch alarm and structured logging for PlayCardFunction

**Architecture Reference**: Section 8.3 — Logging & Observability; Section 10.2 — Responsiveness (≤ 300 ms p95)

AS A DevOps engineer
I WANT PlayCardFunction to emit structured logs and have a CloudWatch error alarm
SO THAT card-play failures are observable and latency can be tracked against the 300 ms p95 target

#### SCENARIO 1: Structured log emitted on every invocation

**Scenario ID**: GAME-INFRA-001.4-S1

**GIVEN**
* PlayCardFunction uses AWS Lambda Powertools `Logger` and `Tracer`

**WHEN**
* A card play is processed (success or rule violation)

**THEN**
* A JSON log entry appears in `/aws/lambda/PlayCardFunction` containing `gameId`, `playerId`, `action`, and `durationMs`
* An X-Ray trace links API Gateway → Lambda → DynamoDB

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors

**Scenario ID**: GAME-INFRA-001.4-S2

**GIVEN**
* A CloudWatch alarm is defined on `Errors` metric for `PlayCardFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* PlayCardFunction throws an unhandled exception

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds

---

## Implementation Order

```
GAME-INFRA-001.1 (Lambda deploy)
  → GAME-INFRA-001.2 (DynamoDB IAM + conditional write)
  → GAME-INFRA-001.3 (playCard route)
  → GAME-INFRA-001.4 (monitoring)
  → GAME-BE-001.2 (play_card() pure domain function)
  → GAME-BE-001.1 (PlayCardFunction handler + use case)
  → GAME-FE-001.1 (game board hand rendering + interaction)
  → GAME-STORY-001 (E2E: play card, verify state update and both players notified)
```
