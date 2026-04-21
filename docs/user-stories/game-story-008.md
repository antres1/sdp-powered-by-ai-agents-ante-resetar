# GAME-STORY-008: Shared Domain Code Packaged as Lambda Layer

**Architecture Reference**: Section 9 — ADR-005 (shared domain code as Lambda Layer); Section 4.2 — Hexagonal Architecture (domain layer has zero infrastructure imports); Section 7.2 — Infrastructure as Code
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A developer
I WANT the shared domain code (`GameState`, `Game Rules`, `RuleViolation`) packaged as a Lambda Layer
SO THAT all Lambda functions share a single copy of the domain logic without duplication in each deployment package

### SCENARIO 1: All game Lambdas import domain code from the shared layer

**Scenario ID**: GAME-STORY-008-S1

**GIVEN**
* The Lambda Layer containing the domain package is deployed
* PlayCardFunction, EndTurnFunction, MatchmakingFunction, and RejoinFunction reference the layer

**WHEN**
* Any of these Lambdas is invoked

**THEN**
* The domain module is importable (`from domain.game import play_card, end_turn, is_game_over`)
* No `ImportError` is raised
* The Lambda executes successfully

### SCENARIO 2: Domain layer has zero infrastructure imports

**Scenario ID**: GAME-STORY-008-S2

**GIVEN**
* The domain package source files are inspected

**WHEN**
* A static analysis check runs (e.g. `grep -r "boto3\|aws_lambda_powertools" domain/`)

**THEN**
* No AWS SDK or infrastructure imports are found in any domain module
* The domain package can be imported in a plain Python environment with no AWS dependencies

---

## Frontend Sub-Stories

*No frontend sub-story: this story is purely a build/infrastructure concern with no UI impact.*

---

## Backend Sub-Stories

### GAME-BE-008.1: Domain package structured for Lambda Layer compatibility

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 9 — ADR-004, ADR-005

AS A developer
I WANT the domain package laid out under `python/domain/` so it is importable from a Lambda Layer
SO THAT the layer structure matches the Lambda runtime's `PYTHONPATH` convention

#### SCENARIO 1: Domain modules importable after layer attachment

**Scenario ID**: GAME-BE-008.1-S1

**GIVEN**
* The layer zip contains `python/domain/__init__.py`, `python/domain/game.py`, and `python/domain/models.py`
* A Lambda function has the layer attached

**WHEN**
* The Lambda runtime initialises

**THEN**
* `import domain.game` succeeds
* `from domain.models import GameState, RuleViolation` succeeds

#### SCENARIO 2: Domain functions are pure — no side effects, no AWS imports

**Scenario ID**: GAME-BE-008.1-S2

**GIVEN**
* The domain package is installed in a plain Python 3.12 virtual environment (no boto3)

**WHEN**
* `from domain.game import play_card, end_turn, is_game_over` is executed

**THEN**
* No `ImportError` or `ModuleNotFoundError` is raised
* All three functions are callable

---

## Infrastructure Sub-Stories

### GAME-INFRA-008.1: Dockerfile builds successfully for the game service

**Architecture Reference**: Section 9 — ADR-005 (shared domain code); Section 4.2 — Hexagonal Architecture; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the game service Dockerfile to build without errors
SO THAT the container image is available for local development and test execution

#### SCENARIO 1: Docker image builds from project root

**Scenario ID**: GAME-INFRA-008.1-S1

**GIVEN**
* A `Dockerfile` exists at the project root targeting Python 3.12
* The `src/` directory contains the domain package under `src/domain/`

**WHEN**
* `docker build -t tcg-game .` is executed

**THEN**
* The build completes with exit code 0
* `docker images tcg-game` lists the image

---

### GAME-INFRA-008.2: Dependencies are installed correctly inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 9 — ADR-004, ADR-005

AS A DevOps engineer
I WANT all Python dependencies declared in `requirements.txt` to be installed inside the Docker image
SO THAT the domain package and its test suite can import every required package without errors

#### SCENARIO 1: Domain package importable with no AWS dependencies

**Scenario ID**: GAME-INFRA-008.2-S1

**GIVEN**
* `requirements.txt` lists only pure-Python test and runtime dependencies (no boto3)
* The Dockerfile runs `pip install -r requirements.txt`

**WHEN**
* `docker run --rm tcg-game python -c "from domain.game import play_card, end_turn, is_game_over; from domain.models import GameState, RuleViolation"` is executed

**THEN**
* The command exits with code 0
* No `ModuleNotFoundError`, `ImportError`, or AWS-related import error is printed

---

### GAME-INFRA-008.3: Project structure supports pytest discovery inside the container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 9 — ADR-005

AS A DevOps engineer
I WANT the project layout to follow pytest conventions so that test collection succeeds inside the container
SO THAT `pytest` can discover domain package tests without manual path configuration

#### SCENARIO 1: pytest collects domain tests without import errors

**Scenario ID**: GAME-INFRA-008.3-S1

**GIVEN**
* Test files reside under `tests/` and are named `test_*.py`
* A `conftest.py` or `pyproject.toml` sets the `pythonpath` to `src/`
* The domain package is at `src/domain/`

**WHEN**
* `docker run --rm tcg-game pytest --collect-only` is executed

**THEN**
* pytest prints a list of collected test items including domain package tests
* Exit code is 0 and no `ImportError` appears in the output

---

### GAME-INFRA-008.4: Test suite passes inside the Docker container

**Architecture Reference**: Section 4.2 — Hexagonal Architecture; Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the full pytest suite to run and pass inside the Docker container
SO THAT the domain package is verified as correct and free of AWS imports before any deployment step

#### SCENARIO 1: pytest exits with code 0 inside the container

**Scenario ID**: GAME-INFRA-008.4-S1

**GIVEN**
* The Docker image has been built successfully (GAME-INFRA-008.1)
* All dependencies are installed (GAME-INFRA-008.2)
* Test discovery succeeds (GAME-INFRA-008.3)

**WHEN**
* `docker run --rm tcg-game pytest` is executed

**THEN**
* All tests pass including domain package purity tests
* The process exits with code 0
* Test output is visible in the container's stdout log

---

## Implementation Order

```
GAME-INFRA-008.1 (Dockerfile builds)
  → GAME-INFRA-008.2 (dependencies installed, domain importable without AWS)
  → GAME-INFRA-008.3 (pytest discovery)
  → GAME-INFRA-008.4 (test suite passes in container)
  → GAME-BE-008.1 (structure domain package under src/domain/ for layer compatibility)
  → GAME-STORY-008 (E2E: deploy stack, invoke each Lambda, verify domain imports succeed)
```
