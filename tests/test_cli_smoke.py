import json
import subprocess
import sys
from pathlib import Path


def _run(db: Path, *args: str) -> dict:
    root = Path(__file__).resolve().parent.parent
    env = {"PYTHONPATH": str(root / "src"), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        [sys.executable, "-m", "app", "--db", str(db), *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


def test_cli_smoke_full_match_and_first_turn(tmp_path):
    db = tmp_path / "tcg.db"

    # first player joins -> waiting
    waiting = _run(db, "join", "--player", "A")
    assert waiting["status"] == "waiting"

    # second player joins -> matched
    matched = _run(db, "join", "--player", "B")
    assert matched["status"] == "matched"
    game_id = matched["game"]["game_id"]

    # A (active) plays card index 0 (cost 0 per STARTING_DECK)
    played = _run(db, "play", "--game", game_id, "--player", "A", "--card", "0")
    assert played["error"] is None
    assert played["winner"] is None

    # A ends turn -> B becomes active
    ended = _run(db, "end-turn", "--game", game_id, "--player", "A")
    assert ended["error"] is None
    status = _run(db, "status", "--game", game_id)
    assert status["active_player_index"] == 1
    # B drew a card so their hand grew by one
    assert len(status["players"][1]["hand"]) == 4
