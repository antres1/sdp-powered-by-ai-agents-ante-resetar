# GAME-STORY-001: Player Plays a Card

**Architecture Reference**: Section 6 — Runtime View, Scenario 2 (Play Card); Section 5.2 — Level 2 Components (action handlers); Section 8.2 — Error Handling; Section 8.4 — Game State Consistency
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
* The game state is unchanged (no SQLite write)
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

### GAME-BE-001.1: the play_card handler applies card-play domain logic

**Architecture Reference**: Section 5.2 — Game Use Case, Game Rules, GameRepository, PlayerNotifier

AS A system
I WANT the play_card handler to load game state, delegate to the domain `play_card()` pure function, persist the result, and notify both players
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
* the play_card handler is invoked

**THEN**
* The domain `play_card()` is never called
* Only the acting player receives `{"error": "not your turn"}`
* No SQLite write occurs

### GAME-BE-001.2: `play_card()` pure domain function

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 4.2 — Hexagonal Architecture

AS A developer
I WANT a pure `play_card(state, card_index)` function with no infrastructure imports
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

### GAME-INFRA-001.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 5.2 — Level 2 Components (action handlers); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-001.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-001.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 8.4 — Game State Consistency

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the game service and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-001.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-001.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Level 2 Components (Game Rules); Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover all test files without manual path configuration

#### SCENARIO 1: pytest collects tests without import errors

**Scenario ID**: GAME-INFRA-001.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-001.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Game Rules (pure functions); Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-001.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-001.1)
* All dependencies are installed (GAME-INFRA-001.2)
* Test discovery succeeds (GAME-INFRA-001.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-001.1 (Dockerfile builds)
  → GAME-INFRA-001.2 (dependencies installed)
  → GAME-INFRA-001.3 (pytest discovery)
  → GAME-INFRA-001.4 (test suite passes in container)
  → GAME-BE-001.2 (play_card() pure domain function)
  → GAME-BE-001.1 (the play_card handler handler + use case)
  → GAME-FE-001.1 (game board hand rendering + interaction)
  → GAME-STORY-001 (E2E: play card, verify state update and both players notified)
```
