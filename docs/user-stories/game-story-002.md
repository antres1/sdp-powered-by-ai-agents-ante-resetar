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

### GAME-INFRA-002.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-002.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including `end_turn` logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-002.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the end-turn service and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-002.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-002.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover end-turn test files without manual path configuration

#### SCENARIO 1: pytest collects end-turn tests without import errors

**Scenario ID**: GAME-INFRA-002.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including end-turn tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-002.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-002.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-002.1)
* All dependencies are installed (GAME-INFRA-002.2)
* Test discovery succeeds (GAME-INFRA-002.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including end-turn scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-002.1 (Dockerfile builds)
  → GAME-INFRA-002.2 (dependencies installed)
  → GAME-INFRA-002.3 (pytest discovery)
  → GAME-INFRA-002.4 (test suite passes in container)
  → GAME-BE-002.2 (end_turn() pure domain function)
  → GAME-BE-002.1 (EndTurnFunction handler + use case)
  → GAME-FE-002.1 (End Turn button + turn indicator)
  → GAME-STORY-002 (E2E: end turn, verify mana/draw/switch and both players notified)
```
