# 9. Architecture Decisions

## ADR-001: Use Python with AWS Lambda for Game Logic

**Status:** Accepted

**Context:**
The Trading Card Game needs a runtime for implementing game rules (turns, mana,
card play, damage, win conditions) and exposing them via API. The project already
uses Python tooling (Black, Ruff, isort, Bandit) and targets a serverless deployment.

**Decision:**
Use Python 3.12 on AWS Lambda for all backend logic.

**Rationale:**
- Matches existing project tooling
- Lambda provides per-invocation scaling — no idle servers during off-peak
- Python's expressiveness suits rule-heavy domain logic (turn sequencing, mana accounting, special mechanics like Bleeding Out and Overload)
- Large ecosystem for testing (pytest, pytest-bdd) aligns with TDD/BDD approach

**Consequences:**
- Cold starts add latency on first invocation (~200–500 ms)
- Lambda's 15-minute timeout is irrelevant for short game actions but rules out long-polling designs

---

## ADR-002: Use DynamoDB Single-Table Design for Game State

**Status:** Accepted

**Context:**
The game needs to persist player sessions, active game state (hands, decks, mana,
health), and connection mappings. Access patterns are known upfront: look up game
by ID, look up player's active connection, find waiting players in queue.

**Decision:**
Use Amazon DynamoDB with single-table design. All entities (Game, Connection, Queue)
share one table using composite keys (PK/SK).

**Rationale:**
- Scales to zero with on-demand billing — no cost when nobody is playing
- Single-digit millisecond reads for game state lookups
- No connection pooling needed — fits Lambda's ephemeral model
- Single table reduces operational overhead (one backup policy, one set of alarms)
- Known access patterns make single-table design feasible

**Consequences:**
- Access patterns must be designed upfront; ad-hoc queries require GSIs or scans
- Team needs to learn DynamoDB single-table patterns (overloaded keys)

---

## ADR-003: Use WebSocket API Gateway for Real-Time Gameplay

**Status:** Accepted

**Context:**
The game is turn-based and multiplayer. When one player plays a card or ends their
turn, the opponent must see the result immediately. HTTP polling would add latency
and unnecessary cost.

**Decision:**
Use AWS API Gateway WebSocket APIs to push game state updates to connected players
in real time.

**Rationale:**
- Native AWS integration with Lambda — each WebSocket event triggers a Lambda
- Players receive opponent actions instantly without polling
- Connection management handled by API Gateway — no server to maintain
- Cost-effective: pay per message, not per open connection

**Consequences:**
- Connection state (`connectionId` ↔ `playerId`) must be tracked in DynamoDB
- Reconnection logic needed in the client for dropped connections
- Adds complexity compared to REST — must handle connection lifecycle

---

## ADR-004: Hexagonal Architecture for Lambda Handlers

**Status:** Accepted

**Context:**
Game rules (mana, Bleeding Out, Overload, win condition) must be unit-testable
without deploying to AWS or mocking boto3. Mixing domain logic with AWS SDK calls
makes tests slow and brittle.

**Decision:**
Apply Hexagonal (Ports & Adapters) architecture inside each Lambda. The domain
layer (`GameState`, `Game Rules`) has zero infrastructure imports. Adapters
(`GameRepository`, `PlayerNotifier`) implement ports and are injected at the
handler level.

**Rationale:**
- Domain logic tested with plain `pytest` — no mocks, no network
- Adapters can be swapped (e.g. in-memory repo for local dev)
- Aligns with single-responsibility-per-Lambda principle

**Consequences:**
- Slightly more files per Lambda (handler, use case, domain, adapters)
- Developers must respect the dependency rule: domain never imports adapters

---

## ADR-005: One Lambda per Game Action

**Status:** Accepted

**Context:**
A single "game handler" Lambda could route all actions internally. However, this
creates a monolith that is harder to test, deploy, and reason about independently.

**Decision:**
Each WebSocket route (`$connect`, `$disconnect`, `joinQueue`, `playCard`,
`endTurn`) maps to its own Lambda function.

**Rationale:**
- Independent deploy and scaling per action
- Failure in one action does not affect others
- IAM permissions scoped to minimum needed per function
- Aligns with single-responsibility principle (TC-2, OC-2)

**Consequences:**
- More SAM resources to define (mitigated by SAM's `Globals` section)
- Shared domain code must be packaged as a Lambda Layer or included in each deployment package
