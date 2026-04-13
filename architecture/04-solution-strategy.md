# 4. Solution Strategy

## 4.1 Key Decisions

| Goal | Strategy |
|------|----------|
| Correctness | Pure-function domain layer; all rules tested without AWS |
| Real-time responsiveness | WebSocket API Gateway pushes state to both players after every action |
| Testability | Hexagonal architecture — domain core has zero infrastructure imports |
| Scalability | Serverless Lambda + DynamoDB on-demand; scales to zero and to burst |
| Operability | SAM templates for all infra; structured logging via AWS Lambda Powertools |

## 4.2 Architecture Style

**Hexagonal (Ports & Adapters)** within each Lambda:

```
┌─────────────────────────────────────┐
│  Lambda Handler (adapter/in)        │
│    ↓                                │
│  Domain Layer (pure Python)         │
│    ↓                                │
│  Repository / Notifier (adapter/out)│
└─────────────────────────────────────┘
```

- The domain layer (`game/`, `matchmaking/`) contains all rules and has no AWS imports.
- Adapters translate between AWS events/SDK calls and domain objects.

## 4.3 Bounded Contexts

| Context | Responsibility |
|---------|---------------|
| **Game Engine** | Turn sequencing, mana, card play, damage, win condition |
| **Matchmaking** | Pairing waiting players into a new game session |
| **Connection Management** | Tracking WebSocket `connectionId` ↔ `playerId` in DynamoDB |

## 4.4 Data Flow (one turn)

1. Player sends `playCard` action over WebSocket.
2. API Gateway routes to `PlayCardFunction` Lambda.
3. Lambda loads game state from DynamoDB, delegates to domain layer.
4. Domain returns updated `GameState` (or raises a rule violation).
5. Lambda persists new state to DynamoDB.
6. Lambda posts updated state to both players via API Gateway Management API.
