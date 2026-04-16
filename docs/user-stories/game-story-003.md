# GAME-STORY-003: Game Detects Win Condition

**Architecture Reference**: Section 6 — Runtime View, Scenario 2 (Play Card, game_over branch) and Scenario 3 (End Turn, Bleeding Out death branch); Section 5.2 — Game Rules (win condition); Section 8.2 — Error Handling
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT the game to detect when a player's health drops to 0 or below and declare a winner
SO THAT the game ends correctly and both players are informed of the outcome

### SCENARIO 1: Win by card damage — opponent health reaches 0

**Scenario ID**: GAME-STORY-003-S1

**GIVEN**
* The opponent has 2 HP remaining
* The active player plays a card with cost ≥ 2

**WHEN**
* The card play is processed

**THEN**
* The opponent's HP drops to ≤ 0
* Both players receive `{"status": "game_over", "winner": "<activePlayerId>"}`
* No further actions are accepted for this game

### SCENARIO 2: Win by Bleeding Out — opponent health reaches 0 on end turn

**Scenario ID**: GAME-STORY-003-S2

**GIVEN**
* The opponent has 1 HP remaining and an empty deck

**WHEN**
* The active player sends `{"action": "endTurn"}`

**THEN**
* Bleeding Out reduces the opponent's HP to 0
* Both players receive `{"status": "game_over", "winner": "<activePlayerId>"}`

---

## Frontend Sub-Stories

### GAME-FE-003.1: Game over screen

AS A player
I WANT a game over screen that shows whether I won or lost
SO THAT I know the outcome and can return to the lobby

#### SCENARIO 1: Winner sees victory screen

**Scenario ID**: GAME-FE-003.1-S1

**GIVEN**
* A `{"status": "game_over", "winner": "<myPlayerId>"}` message arrives

**WHEN**
* The UI processes the message

**THEN**
* The game board is replaced with a "You Win!" screen
* A "Return to Lobby" button is displayed

#### SCENARIO 2: Loser sees defeat screen

**Scenario ID**: GAME-FE-003.1-S2

**GIVEN**
* A `{"status": "game_over", "winner": "<opponentPlayerId>"}` message arrives

**WHEN**
* The UI processes the message

**THEN**
* The game board is replaced with a "You Lose" screen
* A "Return to Lobby" button is displayed

---

## Backend Sub-Stories

### GAME-BE-003.1: `is_game_over()` pure domain function

**Architecture Reference**: Section 5.2 — Game Rules (win condition); Section 4.2 — Hexagonal Architecture

AS A developer
I WANT a pure `is_game_over(state)` function that returns the winner's player ID or `None`
SO THAT the win condition is unit-testable without infrastructure

#### SCENARIO 1: Returns winner when a player's HP ≤ 0

**Scenario ID**: GAME-BE-003.1-S1

**GIVEN**
* A `GameState` where player B has HP = 0

**WHEN**
* `is_game_over(state)` is called

**THEN**
* Returns player A's ID (the surviving player)

#### SCENARIO 2: Returns None when both players have HP > 0

**Scenario ID**: GAME-BE-003.1-S2

**GIVEN**
* A `GameState` where both players have HP > 0

**WHEN**
* `is_game_over(state)` is called

**THEN**
* Returns `None`

### GAME-BE-003.2: PlayCardFunction and EndTurnFunction broadcast game_over

**Architecture Reference**: Section 6 — Runtime View, Scenario 2 and 3 (game_over branch)

AS A system
I WANT PlayCardFunction and EndTurnFunction to check `is_game_over()` after every state change and broadcast the result
SO THAT the game ends immediately when the win condition is met

#### SCENARIO 1: game_over broadcast after lethal card play

**Scenario ID**: GAME-BE-003.2-S1

**GIVEN**
* `play_card()` returns a new `GameState` where the opponent's HP ≤ 0

**WHEN**
* The handler checks `is_game_over(new_state)`

**THEN**
* `PlayerNotifier.post_to_connection()` is called for both players with `{"status": "game_over", "winner": "<winnerId>"}`
* The game state is still persisted (final state recorded)

#### SCENARIO 2: game_over broadcast after Bleeding Out on end turn

**Scenario ID**: GAME-BE-003.2-S2

**GIVEN**
* `end_turn()` returns a new `GameState` where the drawing player's HP ≤ 0 (Bleeding Out)

**WHEN**
* The handler checks `is_game_over(new_state)`

**THEN**
* Both players receive `{"status": "game_over", "winner": "<winnerId>"}`

---

## Infrastructure Sub-Stories

### GAME-INFRA-003.1: Lambda compute — no new Lambda required

**Architecture Reference**: Section 5.1 — PlayCardFunction, EndTurnFunction (win condition is handled within existing Lambdas)

AS A DevOps engineer
I WANT to confirm that win condition detection runs inside the existing PlayCardFunction and EndTurnFunction Lambdas
SO THAT no additional compute resource is needed for this story

#### SCENARIO 1: Win condition check executes within existing Lambda invocation

**Scenario ID**: GAME-INFRA-003.1-S1

**GIVEN**
* PlayCardFunction and EndTurnFunction are deployed (GAME-STORY-001, GAME-STORY-002)

**WHEN**
* A lethal action is processed

**THEN**
* The `game_over` message is sent within the same Lambda invocation, before the function returns
* No additional Lambda function is invoked

---

### GAME-INFRA-003.2: DynamoDB — final game state persisted on game over

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Game); Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT the final game state (with the losing player at ≤ 0 HP) to be written to DynamoDB before the game_over message is sent
SO THAT the outcome is durable and auditable

#### SCENARIO 1: Final state item exists in DynamoDB after game over

**Scenario ID**: GAME-INFRA-003.2-S1

**GIVEN**
* A lethal card play or Bleeding Out event occurs

**WHEN**
* The Lambda completes

**THEN**
* A `GetItem` on `GAME#<gameId> / STATE` returns the final state with the losing player's HP ≤ 0

---

### GAME-INFRA-003.3: WebSocket delivery of game_over to both connections

**Architecture Reference**: Section 6 — Runtime View (game_over branch); Section 8.5 — WebSocket Connection Lifecycle

AS A DevOps engineer
I WANT the `game_over` message delivered to both players' WebSocket connections via the Management API
SO THAT both players receive the outcome in real time

#### SCENARIO 1: game_over message delivered to both connections

**Scenario ID**: GAME-INFRA-003.3-S1

**GIVEN**
* Both players have active WebSocket connections
* A lethal action is processed

**WHEN**
* The Lambda calls `postToConnection` for both `connectionId`s with the `game_over` payload

**THEN**
* Both clients receive the `game_over` message within 500 ms of the action (p95 per Section 10.1)

---

### GAME-INFRA-003.4: CloudWatch — game_over events logged and observable

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT game over events to appear in structured logs
SO THAT game outcomes are auditable and anomalies (e.g. no game_over ever sent) are detectable

#### SCENARIO 1: game_over event logged with winner and gameId

**Scenario ID**: GAME-INFRA-003.4-S1

**GIVEN**
* A game ends (win condition met)

**WHEN**
* The Lambda completes

**THEN**
* A JSON log entry in CloudWatch contains `gameId`, `winnerId`, `action: "game_over"`, and `durationMs`

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors during game-over processing

**Scenario ID**: GAME-INFRA-003.4-S2

**GIVEN**
* A CloudWatch alarm is defined on the `Errors` metric for `PlayCardFunction` or `EndTurnFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* An unhandled exception occurs while processing a lethal action

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds

---

## Implementation Order

```
GAME-INFRA-003.2 (verify DynamoDB final state persistence — reuses existing table)
  → GAME-INFRA-003.1 (confirm no new Lambda needed)
  → GAME-INFRA-003.3 (WebSocket game_over delivery — reuses existing API GW)
  → GAME-INFRA-003.4 (logging)
  → GAME-BE-003.1 (is_game_over() pure domain function)
  → GAME-BE-003.2 (wire is_game_over() into PlayCardFunction + EndTurnFunction handlers)
  → GAME-FE-003.1 (game over screen)
  → GAME-STORY-003 (E2E: lethal card play → both players receive game_over)
```
