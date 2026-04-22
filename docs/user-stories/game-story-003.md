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

### GAME-INFRA-003.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (Game Engine Lambdas); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-003.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including `is_game_over` logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-003.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the win-condition logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-003.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; from domain.game import is_game_over"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-003.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Game Rules (win condition); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover win-condition test files without manual path configuration

#### SCENARIO 1: pytest collects win-condition tests without import errors

**Scenario ID**: GAME-INFRA-003.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including win-condition tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-003.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-003.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-003.1)
* All dependencies are installed (GAME-INFRA-003.2)
* Test discovery succeeds (GAME-INFRA-003.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including win-condition scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-003.1 (Dockerfile builds)
  → GAME-INFRA-003.2 (dependencies installed)
  → GAME-INFRA-003.3 (pytest discovery)
  → GAME-INFRA-003.4 (test suite passes in container)
  → GAME-BE-003.1 (is_game_over() pure domain function)
  → GAME-BE-003.2 (wire is_game_over() into PlayCardFunction + EndTurnFunction handlers)
  → GAME-FE-003.1 (game over screen)
  → GAME-STORY-003 (E2E: lethal card play → both players receive game_over)
```
