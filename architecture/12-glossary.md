# 12. Glossary

| Term | Definition |
|------|-----------|
| **Active Player** | The player whose turn it currently is; only they may play cards or end the turn |
| **Bleeding Out** | Rule: drawing a card from an empty deck deals 1 damage to the drawing player instead |
| **Bounded Context** | A DDD concept; a named boundary within which a domain model is consistent (e.g. Game Engine, Matchmaking) |
| **connectionId** | A unique identifier assigned by the WebSocket server to each open client connection |
| **Docker Volume** | A named, host-managed storage area mounted into a container; used here to persist the SQLite database across container restarts |
| **GameState** | Immutable value object representing the full state of one game: both players' health, mana slots, mana, hand, deck, and active player |
| **Hexagonal Architecture** | An architectural pattern separating domain logic (centre) from infrastructure (adapters); also called Ports & Adapters |
| **JWT** | JSON Web Token; here signed with a pre-shared secret and validated in-process with PyJWT |
| **Mana** | Resource spent to play cards; refilled to the current mana slot count at the start of each turn |
| **Mana Slots** | The maximum mana a player can hold; incremented by 1 each turn up to a maximum of 10 |
| **Overload** | Rule: if a player's hand already holds 5 cards when they draw, the drawn card is discarded |
| **Pure Function** | A function whose output depends only on its inputs and has no side effects; used for all game rule implementations |
| **RuleViolation** | A domain exception raised when a game action breaks the rules (e.g. insufficient mana) |
| **SQLite** | A file-based relational database; used here as the only persistent store, living on a Docker volume |
