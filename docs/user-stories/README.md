# User Story Inventory — Trading Card Game

## Pareto Progress

```
Pareto Progress: 5/5 core stories (100% of 20% core stories)
Core functionality coverage: ~80% of 80% target ✅
Supporting stories written: 7/7 (100%)
Total stories written: 12/12 ✅
```

## Domains

| Domain | Bounded Context |
|--------|----------------|
| CONN | Connection Management |
| MATCH | Matchmaking |
| GAME | Game Engine |

---

## Story List

### CORE Stories (20% → 80% value)

| Story ID | Title | Written | Impl Status | File |
|----------|-------|---------|-------------|------|
| CONN-STORY-001 | Player connects via WebSocket with JWT auth | ✅ | DONE (BE; FE deferred) | [conn-story-001.md](conn-story-001.md) |
| MATCH-STORY-001 | Player joins queue and gets matched | ✅ | DONE (BE; FE + race deferred) | [match-story-001.md](match-story-001.md) |
| GAME-STORY-001 | Player plays a card | ✅ | DONE (BE; FE deferred) | [game-story-001.md](game-story-001.md) |
| GAME-STORY-002 | Player ends their turn | ✅ | DONE (BE; FE deferred) | [game-story-002.md](game-story-002.md) |
| GAME-STORY-003 | Game detects win condition | ✅ | TODO | [game-story-003.md](game-story-003.md) |

### SUPPORTING Stories (80% → remaining 20% value)

| Story ID | Title | Written | Impl Status | File |
|----------|-------|---------|-------------|------|
| CONN-STORY-002 | Player disconnects cleanly | ✅ | TODO | [conn-story-002.md](conn-story-002.md) |
| GAME-STORY-004 | Rule violation: insufficient mana rejected | ✅ | TODO | [game-story-004.md](game-story-004.md) |
| GAME-STORY-005 | Bleeding Out deals 1 damage on empty deck draw | ✅ | TODO | [game-story-005.md](game-story-005.md) |
| GAME-STORY-006 | Overload discards card when hand is full | ✅ | TODO | [game-story-006.md](game-story-006.md) |
| MATCH-STORY-002 | Player waits in queue with no opponent | ✅ | TODO | [match-story-002.md](match-story-002.md) |
| GAME-STORY-007 | Reconnect restores in-progress game session | ✅ | TODO | [game-story-007.md](game-story-007.md) |
| GAME-STORY-008 | Shared domain code packaged as a Python package | ✅ | TODO | [game-story-008.md](game-story-008.md) |

---

## Pareto Rationale

| Story ID | MVP Gate | Blocker | Critical Path | Arch Coverage |
|----------|----------|---------|---------------|---------------|
| CONN-STORY-001 | ✅ | Blocks all others | ✅ | WebSocket server + SQLite + JWT validation |
| MATCH-STORY-001 | ✅ | Blocks GAME-* | ✅ | WebSocket server + SQLite + WebSocket push |
| GAME-STORY-001 | ✅ | Blocks GAME-003 | ✅ | Full hexagonal stack |
| GAME-STORY-002 | ✅ | Blocks GAME-003 | ✅ | Full hexagonal stack + Bleeding Out/Overload |
| GAME-STORY-003 | ✅ | — | ✅ | Game loop completion |

## Implementation Order (within CORE)

```
CONN-STORY-001 → MATCH-STORY-001 → GAME-STORY-001 → GAME-STORY-002 → GAME-STORY-003
```

Each story bundle implements in order: **INFRA → BE → FE → Original (E2E)**
