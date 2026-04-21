# CONN-STORY-001: Player Connects via WebSocket with JWT Auth

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking); Section 5.1 — Building Block View (ConnectFunction); Section 8.1 — Authentication & Authorisation
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to open a WebSocket connection to the game server using my JWT token
SO THAT I am authenticated and my session is tracked, enabling me to join a game

### SCENARIO 1: Successful connection with valid JWT

**Scenario ID**: CONN-STORY-001-S1

**GIVEN**
* A registered Cognito user holds a valid JWT access token
* The WebSocket API endpoint is deployed and reachable

**WHEN**
* The player opens a WebSocket connection to `wss://<api-id>.execute-api.eu-central-1.amazonaws.com/prod?token=<JWT>`

**THEN**
* The connection is accepted (HTTP 101 Switching Protocols)
* A `CONN#<connectionId> → playerId` record is written to DynamoDB
* The player can send and receive WebSocket frames

### SCENARIO 2: Connection rejected with invalid JWT

**Scenario ID**: CONN-STORY-001-S2

**GIVEN**
* A client presents an expired or malformed JWT

**WHEN**
* The client attempts to open a WebSocket connection

**THEN**
* The connection is rejected with HTTP 401
* No DynamoDB record is written
* The rejection is logged in CloudWatch with the reason

---

## Frontend Sub-Stories

### CONN-FE-001.1: WebSocket connection lifecycle management

AS A player
I WANT the browser client to open, maintain, and reconnect the WebSocket connection automatically
SO THAT I stay connected to the game without manual intervention

#### SCENARIO 1: Client opens connection on page load

**Scenario ID**: CONN-FE-001.1-S1

**GIVEN**
* The player is logged in and holds a valid JWT in local storage
* The game page is loaded in the browser

**WHEN**
* The page initialises

**THEN**
* The client opens a WebSocket connection appending `?token=<JWT>` to the WSS URL
* The connection status indicator shows "Connected"

#### SCENARIO 2: Client displays error on rejected connection

**Scenario ID**: CONN-FE-001.1-S2

**GIVEN**
* The stored JWT is expired

**WHEN**
* The client attempts to connect

**THEN**
* The WebSocket `onerror` / `onclose` event fires
* The UI displays "Authentication failed — please log in again"
* The client does not attempt to reconnect automatically

---

## Backend Sub-Stories

### CONN-BE-001.1: ConnectFunction validates JWT and stores connection mapping

**Architecture Reference**: Section 5.1 — ConnectFunction; Section 8.1 — Authentication & Authorisation

AS A system
I WANT the ConnectFunction Lambda to validate the JWT via Cognito and persist the `connectionId → playerId` mapping
SO THAT subsequent Lambdas can identify which player owns a given connection

#### SCENARIO 1: Valid JWT stores connection record

**Scenario ID**: CONN-BE-001.1-S1

**GIVEN**
* A `$connect` event arrives with a valid JWT in `queryStringParameters.token`
* Cognito returns valid claims including `sub` (playerId)

**WHEN**
* ConnectFunction is invoked

**THEN**
* A DynamoDB item `PK=CONN#<connectionId>, SK=PLAYER` with `playerId` and TTL (+24 h) is written
* The function returns HTTP 200

#### SCENARIO 2: Invalid JWT returns 401 without writing to DynamoDB

**Scenario ID**: CONN-BE-001.1-S2

**GIVEN**
* A `$connect` event arrives with an expired JWT

**WHEN**
* ConnectFunction calls Cognito to validate the token

**THEN**
* Cognito returns an error
* The function returns HTTP 401
* No DynamoDB write is performed
* A structured warning log is emitted with `connectionId` and error reason

---

## Infrastructure Sub-Stories

### CONN-INFRA-001.1: Dockerfile builds successfully for the connection service

**Architecture Reference**: Section 5.1 — Building Block View (ConnectFunction); Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the connection service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: CONN-INFRA-001.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the connection service source code including JWT validation logic

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### CONN-INFRA-001.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 8.1 — Authentication & Authorisation; Section 5.1 — ConnectFunction

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the connection service and its test suite can import every required package without errors

#### SCENARIO 1: All declared packages are importable inside the container

**Scenario ID**: CONN-INFRA-001.2-S1

**GIVEN**
* `requirements.txt` lists all runtime and test dependencies with pinned versions
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "import pytest; import domain.game"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError` or `ImportError` is printed

---

### CONN-INFRA-001.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 5.1 — ConnectFunction; Section 4.2 — Hexagonal Architecture

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover connection service test files without manual path configuration

#### SCENARIO 1: pytest collects connection tests without import errors

**Scenario ID**: CONN-INFRA-001.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including connection tests
* Exit code is 0 and no `ImportError` appears in the output

---

### CONN-INFRA-001.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 5.1 — ConnectFunction; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the container image is verified as correct before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: CONN-INFRA-001.4-S1

**GIVEN**
* The Docker image has been built successfully (CONN-INFRA-001.1)
* All dependencies are installed (CONN-INFRA-001.2)
* Test discovery succeeds (CONN-INFRA-001.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including connection and JWT validation scenarios
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
CONN-INFRA-001.1 (Dockerfile builds)
  → CONN-INFRA-001.2 (dependencies installed)
  → CONN-INFRA-001.3 (pytest discovery)
  → CONN-INFRA-001.4 (test suite passes in container)
  → CONN-BE-001.1 (ConnectFunction logic)
  → CONN-FE-001.1 (client WebSocket lifecycle)
  → CONN-STORY-001 (E2E: connect with JWT, verify DynamoDB record)
```
