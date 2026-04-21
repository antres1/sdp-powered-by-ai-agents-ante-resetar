# MATCH-STORY-001: Player Joins Queue and Gets Matched

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking); Section 5.1 — Building Block View (MatchmakingFunction); Section 5.3 — DynamoDB Access Patterns (Queue entry)
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to join the matchmaking queue after connecting
SO THAT I am paired with an opponent and a game session starts automatically

### SCENARIO 1: Two players match successfully

**Scenario ID**: MATCH-STORY-001-S1

**GIVEN**
* Player A is connected (has a valid `CONN#<connA>` record in DynamoDB)
* Player B is connected (has a valid `CONN#<connB>` record in DynamoDB)
* Player A has already sent `joinQueue` and is waiting

**WHEN**
* Player B sends `{"action": "joinQueue"}`

**THEN**
* Both queue entries are deleted from DynamoDB
* A new `GAME#<gameId> / STATE` item is written with the initial GameState (30 HP, 0 mana slots, shuffled decks)
* Player A receives `{"status": "matched", "gameState": {...}}`
* Player B receives `{"status": "matched", "gameState": {...}}`

### SCENARIO 2: First player to join receives waiting confirmation

**Scenario ID**: MATCH-STORY-001-S2

**GIVEN**
* No other player is in the queue

**WHEN**
* A connected player sends `{"action": "joinQueue"}`

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written to DynamoDB
* The player receives `{"status": "waiting"}`
* No game is created

---

## Frontend Sub-Stories

### MATCH-FE-001.1: Matchmaking UI — queue entry and match notification

AS A player
I WANT the UI to show a "searching for opponent" state and transition to the game board when a match is found
SO THAT I know the system is working and can start playing immediately

#### SCENARIO 1: UI shows waiting state after joining queue

**Scenario ID**: MATCH-FE-001.1-S1

**GIVEN**
* The player is connected and on the lobby screen

**WHEN**
* The player clicks "Find Match"

**THEN**
* The client sends `{"action": "joinQueue"}` over the WebSocket
* The UI displays a "Searching for opponent…" indicator

#### SCENARIO 2: UI transitions to game board on match

**Scenario ID**: MATCH-FE-001.1-S2

**GIVEN**
* The player is in the waiting state

**WHEN**
* A `{"status": "matched", "gameState": {...}}` message arrives over the WebSocket

**THEN**
* The waiting indicator is hidden
* The game board is rendered with the initial game state (both players' HP, mana, hand)

---

## Backend Sub-Stories

### MATCH-BE-001.1: MatchmakingFunction pairs players and creates initial GameState

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 4.3 — Bounded Context: Matchmaking

AS A system
I WANT the MatchmakingFunction to atomically claim a waiting player from the queue, create an initial GameState, and notify both players
SO THAT exactly one game is created per pair with no duplicate matches

#### SCENARIO 1: Match created when opponent is waiting

**Scenario ID**: MATCH-BE-001.1-S1

**GIVEN**
* A `QUEUE / PLAYER#<opponentId>` item exists in DynamoDB
* A `joinQueue` event arrives for a second player

**WHEN**
* MatchmakingFunction executes

**THEN**
* Both queue items are deleted via conditional DynamoDB deletes (race-safe per R-4)
* A `GAME#<gameId> / STATE` item is written with a valid initial GameState: each player has 30 HP, 0 mana slots, 0 mana, a 20-card deck, and an empty hand
* `postToConnection` is called for both players with `{"status": "matched", "gameState": {...}}`

#### SCENARIO 2: No match when queue is empty

**Scenario ID**: MATCH-BE-001.1-S2

**GIVEN**
* The queue is empty

**WHEN**
* MatchmakingFunction handles a `joinQueue` event

**THEN**
* A `QUEUE / PLAYER#<playerId>` item is written
* `postToConnection` is called for the joining player with `{"status": "waiting"}`
* No game item is written

#### SCENARIO 3: Concurrent join race — only one match created

**Scenario ID**: MATCH-BE-001.1-S3

**GIVEN**
* Two `joinQueue` events for different players arrive simultaneously
* Both invocations attempt to claim the same waiting queue entry

**WHEN**
* Both MatchmakingFunction instances execute concurrently

**THEN**
* Exactly one invocation succeeds in deleting the queue entry (conditional delete)
* Exactly one game is created
* The losing invocation writes its own queue entry and returns `{"status": "waiting"}`

---

## Infrastructure Sub-Stories

### MATCH-INFRA-001.1: Dockerfile builds successfully for the matchmaking service

**Architecture Reference**: Section 5.1 — Building Block View (MatchmakingFunction); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the matchmaking service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: MATCH-INFRA-001.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the matchmaking service source code

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### MATCH-INFRA-001.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.3 — Bounded Context: Matchmaking; Section 5.1 — MatchmakingFunction

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the matchmaking service and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: MATCH-INFRA-001.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game; from domain.models import GameState"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### MATCH-INFRA-001.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover matchmaking test files without manual path configuration

#### SCENARIO 1: pytest collects matchmaking tests without import errors

**Scenario ID**: MATCH-INFRA-001.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including matchmaking tests
* Exit code is 0 and no `ImportError` appears in the output

---

### MATCH-INFRA-001.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.1 — MatchmakingFunction; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: MATCH-INFRA-001.4-S1

**GIVEN**
* The Docker image has been built successfully (MATCH-INFRA-001.1)
* All dependencies are installed (MATCH-INFRA-001.2)
* Test discovery succeeds (MATCH-INFRA-001.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including matchmaking and race-condition scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
MATCH-INFRA-001.1 (Dockerfile builds)
  → MATCH-INFRA-001.2 (dependencies installed)
  → MATCH-INFRA-001.3 (pytest discovery)
  → MATCH-INFRA-001.4 (test suite passes in container)
  → MATCH-BE-001.1 (MatchmakingFunction logic)
  → MATCH-FE-001.1 (lobby UI + match transition)
  → MATCH-STORY-001 (E2E: two clients connect, join queue, verify game created and both notified)
```
