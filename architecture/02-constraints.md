# 2. Architecture Constraints

## 2.1 Technical Constraints

| ID | Constraint | Reason |
|----|-----------|--------|
| TC-1 | Runtime: **Python 3.12** | Project tooling (Black, Ruff, isort, Bandit, pytest) is Python-based |
| TC-2 | Deployment: **single Docker container** (`docker build` + `docker run`) | Module 6 target; no managed cloud services |
| TC-3 | API: **WebSocket server inside the container**, exposed on a host port | Real-time push to both players without polling (ADR-003) |
| TC-4 | Storage: **SQLite on a Docker volume** | File-based, zero-configuration, persists across container restarts (ADR-002) |
| TC-5 | Auth: **JWT signed with a pre-shared key**, validated in-process with PyJWT | No external identity provider needed for the kata |
| TC-6 | IaC: **Dockerfile** (+ optional `docker-compose.yml`) | All build and run steps captured in code; no manual setup |

## 2.2 Organisational Constraints

| ID | Constraint | Reason |
|----|-----------|--------|
| OC-1 | Domain logic must be **infrastructure-free** | Enables fast unit tests with no I/O |
| OC-2 | One handler function per action/event type inside the service | Single-responsibility principle; avoids monolithic dispatch |
| OC-3 | Tests run inside the container via `pytest` | CI and local runs use the same environment |

## 2.3 Conventions

| ID | Convention |
|----|-----------|
| CV-1 | Game rules implemented as **pure functions** — same input always produces same output |
| CV-2 | All game actions modelled as **events** (e.g. `CardPlayed`, `TurnEnded`) |
| CV-3 | ADRs document every significant technology or design choice |
