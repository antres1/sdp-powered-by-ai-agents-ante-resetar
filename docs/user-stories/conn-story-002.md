# CONN-STORY-002: Player Disconnects Cleanly

**Architecture Reference**: Section 5.1 — Building Block View (DisconnectFunction); Section 8.5 — WebSocket Connection Lifecycle; Section 7.2 — Infrastructure as Code (DisconnectFunction)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT my WebSocket connection record to be removed when I disconnect
SO THAT stale connection entries do not accumulate in DynamoDB and the system stays consistent

### SCENARIO 1: Clean disconnect removes connection record

**Scenario ID**: CONN-STORY-002-S1

**GIVEN**
* A `CONN#<connectionId> / PLAYER` item exists in DynamoDB
* The player closes the browser tab or the WebSocket connection drops

**WHEN**
* API Gateway fires the `$disconnect` event

**THEN**
* The `CONN#<connectionId> / PLAYER` item is deleted from DynamoDB
* No error is returned

### SCENARIO 2: Disconnect for unknown connectionId is a no-op

**Scenario ID**: CONN-STORY-002-S2

**GIVEN**
* No `CONN#<connectionId> / PLAYER` item exists (e.g. TTL already expired it)

**WHEN**
* DisconnectFunction is invoked with that `connectionId`

**THEN**
* The function completes without error (idempotent delete)
* A structured log entry records the missing item as a warning

---

## Frontend Sub-Stories

### CONN-FE-002.1: Client handles unexpected disconnection gracefully

AS A player
I WANT the UI to detect a dropped connection and show a reconnecting indicator
SO THAT I am not left staring at a frozen game board

#### SCENARIO 1: UI shows reconnecting state on unexpected close

**Scenario ID**: CONN-FE-002.1-S1

**GIVEN**
* The WebSocket connection is open and a game is in progress

**WHEN**
* The WebSocket `onclose` event fires unexpectedly (not a user-initiated action)

**THEN**
* The UI overlays a "Connection lost — reconnecting…" message
* Game board controls are disabled to prevent actions on a dead connection

---

## Backend Sub-Stories

### CONN-BE-002.1: DisconnectFunction deletes connection record

**Architecture Reference**: Section 5.1 — DisconnectFunction; Section 8.5 — WebSocket Connection Lifecycle

AS A system
I WANT DisconnectFunction to delete the `CONN#<connectionId>` item from DynamoDB on `$disconnect`
SO THAT stale connection mappings are removed promptly (TTL is a fallback, not the primary cleanup)

#### SCENARIO 1: Connection item deleted on disconnect

**Scenario ID**: CONN-BE-002.1-S1

**GIVEN**
* A `$disconnect` event arrives with a known `connectionId`

**WHEN**
* DisconnectFunction executes

**THEN**
* `DeleteItem` is called for `PK=CONN#<connectionId>, SK=PLAYER`
* The function returns HTTP 200

#### SCENARIO 2: GoneException from postToConnection handled in other Lambdas

**Scenario ID**: CONN-BE-002.1-S2

**GIVEN**
* A game-action Lambda calls `postToConnection` for a `connectionId` that has already disconnected

**WHEN**
* API Gateway Management API returns `GoneException`

**THEN**
* The Lambda catches `GoneException`, deletes the stale connection item, logs a warning, and does not fail the overall action (per Section 8.5)

---

## Infrastructure Sub-Stories

### CONN-INFRA-002.1: Dockerfile builds successfully for the connection service

**Architecture Reference**: Section 5.1 — Building Block View (DisconnectFunction); Section 8.5 — WebSocket Connection Lifecycle

AS A DevOps engineer
I WANT the connection service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: CONN-INFRA-002.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the connection service source code including disconnect logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### CONN-INFRA-002.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 8.5 — WebSocket Connection Lifecycle; Section 5.1 — DisconnectFunction

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the disconnect logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: CONN-INFRA-002.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### CONN-INFRA-002.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.1 — DisconnectFunction; Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover disconnect test files without manual path configuration

#### SCENARIO 1: pytest collects disconnect tests without import errors

**Scenario ID**: CONN-INFRA-002.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including disconnect tests
* Exit code is 0 and no `ImportError` appears in the output

---

### CONN-INFRA-002.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.1 — DisconnectFunction; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: CONN-INFRA-002.4-S1

**GIVEN**
* The Docker image has been built successfully (CONN-INFRA-002.1)
* All dependencies are installed (CONN-INFRA-002.2)
* Test discovery succeeds (CONN-INFRA-002.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including disconnect and GoneException scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
CONN-INFRA-002.1 (Dockerfile builds)
  → CONN-INFRA-002.2 (dependencies installed)
  → CONN-INFRA-002.3 (pytest discovery)
  → CONN-INFRA-002.4 (test suite passes in container)
  → CONN-BE-002.1 (DisconnectFunction logic + GoneException handling)
  → CONN-FE-002.1 (disconnection UI indicator)
  → CONN-STORY-002 (E2E: disconnect, verify DynamoDB record removed)
```
