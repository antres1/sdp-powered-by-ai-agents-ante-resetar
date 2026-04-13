# 12. Glossary

| Term | Definition |
|------|-----------|
| **Active Player** | The player whose turn it currently is; only they may play cards or end the turn |
| **Bleeding Out** | Rule: drawing a card from an empty deck deals 1 damage to the drawing player instead |
| **Bounded Context** | A DDD concept; a named boundary within which a domain model is consistent (e.g. Game Engine, Matchmaking) |
| **Cold Start** | The initialisation delay when AWS Lambda runs a function for the first time after a period of inactivity |
| **connectionId** | A unique identifier assigned by API Gateway to each active WebSocket connection |
| **GameState** | Immutable value object representing the full state of one game: both players' health, mana slots, mana, hand, deck, and active player |
| **Hexagonal Architecture** | An architectural pattern separating domain logic (centre) from infrastructure (adapters); also called Ports & Adapters |
| **Lambda Layer** | A reusable package of code or dependencies attached to multiple Lambda functions at deploy time |
| **Mana** | Resource spent to play cards; refilled to the current mana slot count at the start of each turn |
| **Mana Slots** | The maximum mana a player can hold; incremented by 1 each turn up to a maximum of 10 |
| **Overload** | Rule: if a player's hand already holds 5 cards when they draw, the drawn card is discarded |
| **postToConnection** | API Gateway Management API call used by a Lambda to push a message to a specific WebSocket client |
| **Pure Function** | A function whose output depends only on its inputs and has no side effects; used for all game rule implementations |
| **RuleViolation** | A domain exception raised when a game action breaks the rules (e.g. insufficient mana) |
| **Single-Table Design** | A DynamoDB pattern where all entity types share one table, distinguished by PK/SK key patterns |
| **TTL (Time to Live)** | A DynamoDB feature that automatically deletes items after a specified timestamp; used to expire stale connection records |
