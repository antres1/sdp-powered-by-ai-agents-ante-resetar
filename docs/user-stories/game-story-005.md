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

### GAME-INFRA-005.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (action handlers); Section 1.1 — Game Rules (Bleeding Out)

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-005.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including Bleeding Out logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-005.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 1.1 — Bleeding Out rule

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the Bleeding Out logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-005.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; from domain.game import end_turn"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-005.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover Bleeding Out test files without manual path configuration

#### SCENARIO 1: pytest collects Bleeding Out tests without import errors

**Scenario ID**: GAME-INFRA-005.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including Bleeding Out tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-005.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-005.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-005.1)
* All dependencies are installed (GAME-INFRA-005.2)
* Test discovery succeeds (GAME-INFRA-005.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including Bleeding Out scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-005.1 (Dockerfile builds)
  → GAME-INFRA-005.2 (dependencies installed)
  → GAME-INFRA-005.3 (pytest discovery)
  → GAME-INFRA-005.4 (test suite passes in container)
  → GAME-BE-005.1 (Bleeding Out in end_turn() pure function)
  → GAME-FE-005.1 (Bleeding Out UI indicator)
  → GAME-STORY-005 (E2E: end turn with empty deck → opponent HP reduced, both players notified)
```
