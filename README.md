# Trading Card Game Kata

A minimal implementation of the [Trading Card Game Kata](https://codingdojo.org/kata/TradingCardGame/),
built end-to-end with AI agents as part of the Software Development Processes
Powered by AI Agents course.

The system is a single Python service in a Docker container. It exposes its
behaviour through a small CLI (`python -m app ...`) that drives matchmaking
and game handlers. Game state is persisted in a SQLite database on a mounted
Docker volume.

There is no WebSocket server or browser client in this build — a subset of
the architecture's design. All functionality is accessed through the CLI and
the pytest suite.

## What works today

- Matchmaking: two players can join a queue; the second join creates a game.
- Play Card: active player spends mana, deals damage to the opponent.
- End Turn: opponent becomes active, gets +1 mana slot (capped at 10), draws
  a card (Bleeding Out on empty deck, Overload on full hand).
- Win condition: when a player's HP drops to 0 or below, the game records a
  winner and rejects further actions.
- JWT-authenticated connection recording (the `connect` handler writes
  `connection_id → player_id` in SQLite; unused by the CLI but tested).

Story status is tracked in [`docs/user-stories/README.md`](docs/user-stories/README.md).

## Documentation

📚 **[Full Documentation](https://antres1.github.io/sdp-powered-by-ai-agents-ante-resetar/)** — Architecture, user stories, and implementation details.

## Tech Stack

- **Language**: Python 3.12
- **Testing**: pytest
- **Storage**: SQLite
- **Deployment**: Docker
- **Architecture**: Hexagonal (ports & adapters)
- **Domain**: Pure functions, zero infrastructure imports

## Build and run

```bash
docker build -t tcg-game .
```

The default `CMD` runs the pytest suite. The CLI is available by overriding
the entrypoint:

```bash
docker volume create tcg-data
alias tcg='docker run --rm -v tcg-data:/data --entrypoint python tcg-game -m app'
```

(The `tcg-data` volume holds the SQLite file at `/data/tcg.db` so state
survives between invocations.)

## Verify core functionality

### 1. Test suite must be green

```bash
docker run --rm tcg-game
```

Expected: all tests pass. This is the primary functional contract — every
CORE user story (CONN-001, MATCH-001, GAME-001, GAME-002, GAME-003) is
exercised by at least one story-level E2E test through the public handler
API, plus GAME-004 (rule violations).

### 2. Play a game through the CLI

```bash
# Player A joins — queue is empty → waiting
tcg join --player A
# => {"status": "waiting", "game": null}

# Player B joins — A is waiting → matched, game created
tcg join --player B
# => {"status": "matched", "game": {"game_id": "<UUID>", ...}}

# Copy the game_id from the output, then:
GAME=<game_id>

# See the full state
tcg status --game $GAME

# A is active with 1 mana and hand [0, 1, 1]. Play card index 0 (cost 0):
tcg play --game $GAME --player A --card 0
# => opponent HP unchanged (cost 0), A's hand shrinks to [1, 1]

# End A's turn — B becomes active, draws a card, gets 1 mana slot
tcg end-turn --game $GAME --player A

# B plays their free card
tcg play --game $GAME --player B --card 0
```

### 3. Rule enforcement (manually observable)

Using the game from step 2 (A has played, then ended the turn, so B is now
active with mana 1 and hand `[0, 1, 1, 2]`):

```bash
# Insufficient mana: B has 1 mana and tries to play the cost-2 card (index 3)
tcg play --game $GAME --player B --card 3
# => {"error": "not enough mana", "game": null, "winner": null}

# Out-of-turn play: A tries to play while it's B's turn
tcg play --game $GAME --player A --card 0
# => {"error": "not your turn", ...}

# Invalid card index
tcg play --game $GAME --player B --card 99
# => {"error": "invalid card index", ...}
```

### 4. Win condition

Run enough turns until one player is reduced to 0 HP. The next `play` or
`end-turn` response will contain `"winner": "<player_id>"`. After that all
further actions return `{"error": "game over", ...}`.

### 5. Reset

```bash
docker volume rm tcg-data && docker volume create tcg-data
```

## Project layout

```
src/
├── domain/          # Pure game rules (play_card, end_turn, is_game_over)
├── game/            # Handlers that load state, apply rules, persist
├── matchmaking/     # Queue + initial game creation, SQLite repo
├── connection/      # JWT validation + connection_id → player_id mapping
└── app/__main__.py  # CLI entrypoint
tests/               # 41 pytest tests, all green
architecture/        # arc42 chapters (design docs)
docs/user-stories/   # Story bundles + inventory
```

## Run tests outside Docker

```bash
pip install -r requirements.txt
PYTHONPATH=src pytest tests/
```

## Starting deck

Each player starts with a fixed deck `[0, 1, 1, 2, 2, 3, 3, 4, 5, 7]` and
draws 3 cards into their opening hand. Deterministic so tests and manual
play stay reproducible. Player A (the first to join) begins with 1 mana slot
already refilled so the opening turn is immediately playable.
