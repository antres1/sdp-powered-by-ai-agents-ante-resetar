# 9. Architecture Decisions

## ADR-001: Use Python 3.12 in a Docker Container for Game Logic

**Status:** Accepted

**Context:**
The Trading Card Game needs a runtime for implementing game rules (turns, mana,
card play, damage, win conditions) and exposing them via API. The project already
uses Python tooling (Black, Ruff, isort, Bandit) and Module 6 mandates a local
Docker deployment target.

**Decision:**
Use Python 3.12 in a single Docker container (built from `python:3.12-slim`).

**Rationale:**
- Matches existing project tooling
- One container = one build, one run, one test command
- Python's expressiveness suits rule-heavy domain logic (turn sequencing, mana accounting, special mechanics like Bleeding Out and Overload)
- Large ecosystem for testing (pytest, pytest-bdd) aligns with the TDD/BDD approach

**Consequences:**
- No horizontal scaling story — acceptable for a kata
- The container is the only supported deployment artefact

---

## ADR-002: Use SQLite on a Docker Volume for Game State

**Status:** Accepted

**Context:**
The game needs to persist player sessions, active game state (hands, decks, mana,
health), and connection mappings. Access patterns are simple: look up game by ID,
look up player's active connection, find waiting players in queue. The system
must run without any external database server.

**Decision:**
Use SQLite, with the database file stored on a Docker volume mounted at `/data`.

**Rationale:**
- Zero-configuration: SQLite ships with Python
- File on a named volume survives `docker run` restarts
- Access patterns are trivial for a relational store — three small tables
- No network hop, no connection pool, no external service to manage

**Consequences:**
- Single-writer only — fine for a single-process service, but blocks future multi-container scale-out
- Migrations must be handled in application code (no managed schema service)

---

## ADR-003: Use WebSockets for Real-Time Gameplay

**Status:** Accepted

**Context:**
The game is turn-based and multiplayer. When one player plays a card or ends their
turn, the opponent must see the result immediately. HTTP polling would add latency.

**Decision:**
Use a WebSocket server inside the container (e.g. `websockets` or FastAPI's
WebSocket support) to push game state updates to connected players.

**Rationale:**
- Native bi-directional protocol — no polling
- Server holds the open socket and can push messages to either player
- Runs in the same process as the domain logic, minimising latency

**Consequences:**
- Connection state (`connectionId` ↔ `playerId`) must be tracked in SQLite
- Reconnection logic needed in the client for dropped connections
- The server process is stateful with respect to open sockets — it cannot be killed and replaced without disconnecting players

---

## ADR-004: Hexagonal Architecture for Action Handlers

**Status:** Accepted

**Context:**
Game rules (mana, Bleeding Out, Overload, win condition) must be unit-testable
without starting the WebSocket server or hitting SQLite. Mixing domain logic with
I/O makes tests slow and brittle.

**Decision:**
Apply Hexagonal (Ports & Adapters) architecture inside the service. The domain
layer (`GameState`, `Game Rules`) has zero infrastructure imports. Adapters
(`GameRepository`, `PlayerNotifier`) implement ports and are injected at the
handler level.

**Rationale:**
- Domain logic tested with plain `pytest` — no mocks, no network, no DB
- Adapters can be swapped (e.g. in-memory repo for tests)
- Aligns with single-responsibility principle

**Consequences:**
- Slightly more files per action (handler, use case, domain, adapters)
- Developers must respect the dependency rule: domain never imports adapters

---

## ADR-005: One Handler Function per Game Action

**Status:** Accepted

**Context:**
A single "game handler" function could route all actions internally. However, that
creates a hard-to-test monolith and mixes unrelated code paths.

**Decision:**
Each WebSocket action (`connect`, `disconnect`, `joinQueue`, `playCard`,
`endTurn`) maps to its own handler function registered on a router.

**Rationale:**
- Independent testing per action
- Failure in one action does not affect others
- Aligns with single-responsibility principle (TC-2, OC-2)

**Consequences:**
- Router must fan out to N handlers — trivial in Python
- Shared domain code is a plain Python package (`src/domain/`) imported by every handler; no packaging gymnastics required
