# MATCH-STORY-002: Player Waits in Queue with No Opponent

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking, waiting branch); Section 5.1 — Building Block View (MatchmakingFunction); Section 5.3 — DynamoDB Access Patterns (Queue entry)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT to receive a "waiting" confirmation when I join the queue and no opponent is available
SO THAT I know my request was received and the system is looking for a match

### SCENARIO 1: Player receives waiting status when queue is empty

**Scenario ID**: MATCH-STORY-002-S1

**GIVEN**
* No other player is in the matchmaking queue
* A connected player sends `{"action": "joinQueue"}`

**WHEN**
* MatchmakingFunction processes the request

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written to DynamoDB
* The player receives `{"status": "waiting"}`
* No game is created

### SCENARIO 2: Player cannot join queue twice

**Scenario ID**: MATCH-STORY-002-S2

**GIVEN**
* A `QUEUE / PLAYER#<playerId>` item already exists for this player

**WHEN**
* The same player sends `{"action": "joinQueue"}` again

**THEN**
* No duplicate queue entry is written
* The player receives `{"status": "waiting"}` (idempotent response)

---

## Frontend Sub-Stories

### MATCH-FE-002.1: Lobby shows persistent waiting state

AS A player
I WANT the lobby to show a "Searching for opponent…" indicator that persists until a match is found
SO THAT I know the system is still looking and I haven't been dropped from the queue

#### SCENARIO 1: Waiting indicator persists after joining queue

**Scenario ID**: MATCH-FE-002.1-S1

**GIVEN**
* The player clicked "Find Match" and received `{"status": "waiting"}`

**WHEN**
* Time passes without a match

**THEN**
* The "Searching for opponent…" indicator remains visible
* The "Find Match" button is disabled to prevent duplicate queue entries

#### SCENARIO 2: Waiting indicator clears when match is found

**Scenario ID**: MATCH-FE-002.1-S2

**GIVEN**
* The player is in the waiting state

**WHEN**
* A `{"status": "matched", "gameState": {...}}` message arrives

**THEN**
* The waiting indicator is replaced by the game board

---

## Backend Sub-Stories

### MATCH-BE-002.1: MatchmakingFunction writes queue entry and responds with waiting status

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 5.3 — DynamoDB Access Patterns (Queue entry)

AS A system
I WANT MatchmakingFunction to write a queue entry and return `{"status": "waiting"}` when no opponent is available
SO THAT the player is registered for matching and informed of their status

#### SCENARIO 1: Queue entry written and waiting response sent

**Scenario ID**: MATCH-BE-002.1-S1

**GIVEN**
* No `QUEUE / PLAYER#*` items exist in DynamoDB
* A `joinQueue` event arrives

**WHEN**
* MatchmakingFunction executes

**THEN**
* A `PutItem` with `PK=QUEUE, SK=PLAYER#<playerId>` and `connectionId` is written
* `postToConnection` is called for the joining player with `{"status": "waiting"}`
* No game item is written

#### SCENARIO 2: Idempotent re-join — no duplicate entry

**Scenario ID**: MATCH-BE-002.1-S2

**GIVEN**
* A `QUEUE / PLAYER#<playerId>` item already exists

**WHEN**
* The same player sends `joinQueue` again

**THEN**
* A `PutItem` with `ConditionExpression: attribute_not_exists(PK)` either skips or overwrites idempotently
* The player receives `{"status": "waiting"}`
* No game is created

---

## Infrastructure Sub-Stories

### MATCH-INFRA-002.1: Dockerfile builds successfully for the matchmaking service

**Architecture Reference**: Section 5.1 — Building Block View (MatchmakingFunction); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the matchmaking service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: MATCH-INFRA-002.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the matchmaking service source code including the waiting-queue path

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### MATCH-INFRA-002.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 5.3 — DynamoDB Access Patterns (Queue entry)

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the waiting-queue logic and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: MATCH-INFRA-002.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### MATCH-INFRA-002.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover waiting-queue test files without manual path configuration

#### SCENARIO 1: pytest collects waiting-queue tests without import errors

**Scenario ID**: MATCH-INFRA-002.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including waiting-queue tests
* Exit code is 0 and no `ImportError` appears in the output

---

### MATCH-INFRA-002.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: MATCH-INFRA-002.4-S1

**GIVEN**
* The Docker image has been built successfully (MATCH-INFRA-002.1)
* All dependencies are installed (MATCH-INFRA-002.2)
* Test discovery succeeds (MATCH-INFRA-002.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including waiting-queue and idempotent re-join scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
MATCH-INFRA-002.1 (Dockerfile builds)
  → MATCH-INFRA-002.2 (dependencies installed)
  → MATCH-INFRA-002.3 (pytest discovery)
  → MATCH-INFRA-002.4 (test suite passes in container)
  → MATCH-BE-002.1 (waiting path in MatchmakingFunction)
  → MATCH-FE-002.1 (persistent waiting indicator)
  → MATCH-STORY-002 (E2E: join queue alone → receive waiting status, DynamoDB entry exists)
```
