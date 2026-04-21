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

### GAME-INFRA-006.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 1.1 — Game Rules (Overload)

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-006.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including Overload logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-006.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 1.1 — Overload rule

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the Overload logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-006.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; from domain.game import end_turn"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-006.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover Overload test files without manual path configuration

#### SCENARIO 1: pytest collects Overload tests without import errors

**Scenario ID**: GAME-INFRA-006.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including Overload tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-006.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-006.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-006.1)
* All dependencies are installed (GAME-INFRA-006.2)
* Test discovery succeeds (GAME-INFRA-006.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including Overload scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-006.1 (Dockerfile builds)
  → GAME-INFRA-006.2 (dependencies installed)
  → GAME-INFRA-006.3 (pytest discovery)
  → GAME-INFRA-006.4 (test suite passes in container)
  → GAME-BE-006.1 (Overload in end_turn() pure function)
  → GAME-FE-006.1 (Overload UI indicator)
  → GAME-STORY-006 (E2E: end turn with full hand → card discarded, hand stays at 5, both players notified)
```
