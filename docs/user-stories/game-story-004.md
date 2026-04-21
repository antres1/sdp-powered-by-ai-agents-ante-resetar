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

### GAME-INFRA-004.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 8.2 — Error Handling

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-004.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including `RuleViolation`

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-004.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 8.2 — Error Handling

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the rule-violation logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-004.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; from domain.game import play_card; from domain.models import RuleViolation"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-004.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover rule-violation test files without manual path configuration

#### SCENARIO 1: pytest collects rule-violation tests without import errors

**Scenario ID**: GAME-INFRA-004.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including rule-violation tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-004.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-004.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-004.1)
* All dependencies are installed (GAME-INFRA-004.2)
* Test discovery succeeds (GAME-INFRA-004.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including rule-violation scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-004.1 (Dockerfile builds)
  → GAME-INFRA-004.2 (dependencies installed)
  → GAME-INFRA-004.3 (pytest discovery)
  → GAME-INFRA-004.4 (test suite passes in container)
  → GAME-BE-004.1 (RuleViolation in play_card() pure function)
  → GAME-BE-004.2 (handler catches RuleViolation, sends error to acting player only)
  → GAME-FE-004.1 (error toast + card re-enable)
  → GAME-STORY-004 (E2E: play unaffordable card → only acting player sees error, state unchanged)
```
