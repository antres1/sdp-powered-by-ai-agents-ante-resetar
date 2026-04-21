# GAME-STORY-007: Reconnect Restores In-Progress Game Session

**Architecture Reference**: Section 8.5 — WebSocket Connection Lifecycle; Section 8.1 — Authentication & Authorisation; Section 5.3 — DynamoDB Access Patterns (Connection, Game); Section 9 — ADR-003 (reconnection logic needed in client)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT to reconnect to an in-progress game after a dropped WebSocket connection
SO THAT a temporary network interruption does not forfeit my game

### SCENARIO 1: Reconnecting player receives current game state

**Scenario ID**: GAME-STORY-007-S1

**GIVEN**
* A game is in progress with `GAME#<gameId> / STATE` in DynamoDB
* The player's previous WebSocket connection has dropped
* The player reconnects with a valid JWT

**WHEN**
* The player opens a new WebSocket connection and sends `{"action": "joinQueue"}` or a dedicated `{"action": "rejoin"}`

**THEN**
* The new `connectionId` is stored in DynamoDB, replacing the old one
* The player receives `{"status": "rejoined", "gameState": {...}}` with the current game state
* The opponent is notified that the player has reconnected

### SCENARIO 2: Reconnect with no active game returns to lobby

**Scenario ID**: GAME-STORY-007-S2

**GIVEN**
* A player reconnects with a valid JWT
* No active game exists for this player in DynamoDB

**WHEN**
* The player sends `{"action": "rejoin"}`

**THEN**
* The player receives `{"status": "no_active_game"}`
* The client shows the lobby screen

---

## Frontend Sub-Stories

### GAME-FE-007.1: Automatic reconnection with session restore

AS A player
I WANT the client to automatically attempt reconnection after a dropped connection and restore the game board if a game is in progress
SO THAT brief network interruptions are transparent

#### SCENARIO 1: Client reconnects and restores game board

**Scenario ID**: GAME-FE-007.1-S1

**GIVEN**
* The WebSocket `onclose` event fires unexpectedly during a game
* The player still has a valid JWT

**WHEN**
* The client reconnects (with exponential backoff, max 3 attempts)

**THEN**
* A new WebSocket connection is established
* The client sends `{"action": "rejoin"}`
* On receiving `{"status": "rejoined", "gameState": {...}}`, the game board is restored to the current state

#### SCENARIO 2: Client shows lobby after failed reconnect or no active game

**Scenario ID**: GAME-FE-007.1-S2

**GIVEN**
* All reconnection attempts fail or the server returns `{"status": "no_active_game"}`

**WHEN**
* The client processes the response

**THEN**
* The "Connection lost" overlay is dismissed
* The lobby screen is shown

---

## Backend Sub-Stories

### GAME-BE-007.1: RejoinFunction looks up active game and sends current state

**Architecture Reference**: Section 5.1 — ConnectFunction (extended); Section 8.1 — Authentication & Authorisation; Section 5.3 — DynamoDB Access Patterns

AS A system
I WANT a `rejoin` handler to update the connection mapping and return the current game state to the reconnecting player
SO THAT reconnection is handled server-side without requiring a new matchmaking flow

#### SCENARIO 1: Active game found — connection updated and state returned

**Scenario ID**: GAME-BE-007.1-S1

**GIVEN**
* A `GAME#<gameId> / STATE` item exists where `player.id == playerId`
* The player reconnects with a new `connectionId`

**WHEN**
* The `rejoin` handler is invoked

**THEN**
* The `CONN#<newConnectionId> / PLAYER` item is written (new mapping)
* The old `CONN#<oldConnectionId> / PLAYER` item is deleted
* The game state item is updated with the new `connectionId` for this player
* The player receives `{"status": "rejoined", "gameState": {...}}`
* The opponent receives `{"status": "opponent_reconnected"}`

#### SCENARIO 2: No active game — player directed to lobby

**Scenario ID**: GAME-BE-007.1-S2

**GIVEN**
* No game item exists for the reconnecting player

**WHEN**
* The `rejoin` handler is invoked

**THEN**
* The player receives `{"status": "no_active_game"}`
* No game item is written or modified

---

## Infrastructure Sub-Stories

### GAME-INFRA-007.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 8.5 — WebSocket Connection Lifecycle; Section 5.1 — Building Block View (RejoinFunction)

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-007.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the game service source code including rejoin logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-007.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 8.1 — Authentication & Authorisation

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the rejoin logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: GAME-INFRA-007.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### GAME-INFRA-007.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.2 — Level 2 Components; Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover rejoin test files without manual path configuration

#### SCENARIO 1: pytest collects rejoin tests without import errors

**Scenario ID**: GAME-INFRA-007.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including rejoin tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-007.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.2 — Level 2 Components; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-007.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-007.1)
* All dependencies are installed (GAME-INFRA-007.2)
* Test discovery succeeds (GAME-INFRA-007.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including rejoin scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-007.1 (Dockerfile builds)
  → GAME-INFRA-007.2 (dependencies installed)
  → GAME-INFRA-007.3 (pytest discovery)
  → GAME-INFRA-007.4 (test suite passes in container)
  → GAME-BE-007.1 (rejoin handler logic)
  → GAME-FE-007.1 (auto-reconnect with backoff + game board restore)
  → GAME-STORY-007 (E2E: drop connection mid-game, reconnect, verify game state restored)
```
