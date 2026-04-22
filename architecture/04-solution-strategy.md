# 4. Solution Strategy

## 4.1 Key Decisions

| Goal | Strategy |
|------|----------|
| Correctness | Pure-function domain layer; all rules tested without I/O |
| Responsiveness | WebSocket server pushes state to both players after every action |
| Testability | Hexagonal architecture — domain core has zero infrastructure imports |
| Reproducibility | Single Docker image built from `Dockerfile`; `pytest` runs inside it |
| Operability | Logs written to stdout/stderr, captured by `docker logs` |

## 4.2 Architecture Style

**Hexagonal (Ports & Adapters)** inside one process:

```
┌─────────────────────────────────────┐
│  WebSocket Handler (adapter/in)     │
│    ↓                                │
│  Domain Layer (pure Python)         │
│    ↓                                │
│  Repository / Notifier (adapter/out)│
└─────────────────────────────────────┘
```

- The domain layer (`game/`, `matchmaking/`) contains all rules and has no I/O imports.
- Adapters translate between WebSocket frames / SQLite rows and domain objects.

## 4.3 Bounded Contexts

| Context | Responsibility |
|---------|---------------|
| **Game Engine** | Turn sequencing, mana, card play, damage, win condition |
| **Matchmaking** | Pairing waiting players into a new game session |
| **Connection Management** | Tracking WebSocket `connectionId` ↔ `playerId` in SQLite |

## 4.4 Data Flow (one turn)

1. Player sends `playCard` action over WebSocket.
2. The WebSocket server routes the frame to the `play_card` handler.
3. Handler loads game state from SQLite, delegates to the domain layer.
4. Domain returns updated `GameState` (or raises a rule violation).
5. Handler persists new state to SQLite.
6. Handler pushes the updated state to both players over their WebSocket connections.
