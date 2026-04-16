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

### GAME-INFRA-008.1: Build and deploy domain Lambda Layer via SAM

**Architecture Reference**: Section 7.2 — Infrastructure as Code; Section 9 — ADR-005

AS A DevOps engineer
I WANT the domain code built into a Lambda Layer and deployed via SAM
SO THAT all Lambdas reference a single versioned copy of the domain logic

#### SCENARIO 1: Layer deployed and attached to all game Lambdas

**Scenario ID**: GAME-INFRA-008.1-S1

**GIVEN**
* `template.yaml` defines a `DomainLayer` (`AWS::Serverless::LayerVersion`) with `ContentUri: domain/` and `CompatibleRuntimes: [python3.12]`
* PlayCardFunction, EndTurnFunction, MatchmakingFunction, and RejoinFunction reference `DomainLayer` in their `Layers` property

**WHEN**
* `sam build && sam deploy` completes

**THEN**
* The Lambda Layer version exists in the AWS account
* Each function's configuration lists the layer ARN
* A test invocation of each function succeeds without `ImportError`

---

### GAME-INFRA-008.2: DynamoDB — no new table required for this story

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns

AS A DevOps engineer
I WANT to confirm that packaging domain code as a layer requires no DynamoDB changes
SO THAT this story has no storage impact

#### SCENARIO 1: Existing GameTable unchanged after layer deployment

**Scenario ID**: GAME-INFRA-008.2-S1

**GIVEN**
* The `GameTable` is deployed and contains live game data

**WHEN**
* The domain layer is deployed and Lambdas are updated to reference it

**THEN**
* The `GameTable` schema and data are unchanged
* All existing access patterns continue to work

---

### GAME-INFRA-008.3: CI pipeline builds and publishes the layer

**Architecture Reference**: Section 7.3 — Deployment Pipeline

AS A DevOps engineer
I WANT the GitHub Actions CI pipeline to build the domain layer as part of `sam build`
SO THAT every push produces a fresh layer version without manual steps

#### SCENARIO 1: CI pipeline builds layer and deploys successfully

**Scenario ID**: GAME-INFRA-008.3-S1

**GIVEN**
* The `template.yaml` defines `DomainLayer` with `BuildMethod: python3.12`
* A `git push` triggers the CI pipeline

**WHEN**
* The pipeline runs `sam build && sam deploy`

**THEN**
* The layer is built and a new layer version is published
* All Lambda functions are updated to reference the new layer ARN
* The pipeline exits with code 0

---

### GAME-INFRA-008.4: CloudWatch — layer import errors surfaced in Lambda logs

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT any layer import failures to appear as errors in CloudWatch Logs
SO THAT misconfigured layer attachments are immediately detectable

#### SCENARIO 1: ImportError from missing layer appears in CloudWatch

**Scenario ID**: GAME-INFRA-008.4-S1

**GIVEN**
* A Lambda function is deployed without the domain layer attached (misconfiguration)

**WHEN**
* The Lambda is invoked

**THEN**
* An `ImportError` traceback appears in the function's CloudWatch log group
* The Lambda returns HTTP 500

---

## Implementation Order

```
GAME-INFRA-008.1 (build DomainLayer in SAM template, attach to all Lambdas)
  → GAME-INFRA-008.2 (confirm no DynamoDB changes)
  → GAME-INFRA-008.3 (CI pipeline layer build)
  → GAME-INFRA-008.4 (CloudWatch import error observability)
  → GAME-BE-008.1 (structure domain package under python/domain/ for layer compatibility)
  → GAME-STORY-008 (E2E: deploy stack, invoke each Lambda, verify domain imports succeed)
```
