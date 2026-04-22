"""Thin CLI over the existing matchmaking and game handlers.

Persists state in a SQLite file (default: /data/tcg.db; override with TCG_DB).
One command per invocation: join | play | end-turn | status.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from dataclasses import asdict, is_dataclass
from typing import Any

from game.handlers import end_turn_handler, play_card_handler
from matchmaking.handlers import join_queue
from matchmaking.repository import MatchmakingRepository


def _open_repo(db_path: str) -> MatchmakingRepository:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    repo = MatchmakingRepository(conn)
    repo.init_schema()
    return repo


def _dump(obj: Any) -> str:
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(obj, indent=2, sort_keys=True)


def cmd_join(args: argparse.Namespace, repo: MatchmakingRepository) -> int:
    result = join_queue(player_id=args.player, repo=repo, now_epoch=int(time.time()))
    print(_dump(result))
    return 0


def cmd_play(args: argparse.Namespace, repo: MatchmakingRepository) -> int:
    result = play_card_handler(
        game_id=args.game,
        acting_player_id=args.player,
        card_index=args.card,
        repo=repo,
    )
    print(_dump(result))
    return 1 if result.error else 0


def cmd_end_turn(args: argparse.Namespace, repo: MatchmakingRepository) -> int:
    result = end_turn_handler(
        game_id=args.game, acting_player_id=args.player, repo=repo
    )
    print(_dump(result))
    return 1 if result.error else 0


def cmd_status(args: argparse.Namespace, repo: MatchmakingRepository) -> int:
    game = repo.get_game(args.game)
    if game is None:
        print(_dump({"error": "game not found"}))
        return 1
    print(_dump(game))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tcg", description="Trading Card Game CLI")
    parser.add_argument(
        "--db",
        default=os.environ.get("TCG_DB", "/data/tcg.db"),
        help="path to SQLite database",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_join = sub.add_parser("join", help="join the matchmaking queue")
    p_join.add_argument("--player", required=True)
    p_join.set_defaults(func=cmd_join)

    p_play = sub.add_parser("play", help="play a card")
    p_play.add_argument("--game", required=True)
    p_play.add_argument("--player", required=True)
    p_play.add_argument("--card", type=int, required=True, help="index into hand")
    p_play.set_defaults(func=cmd_play)

    p_end = sub.add_parser("end-turn", help="end your turn")
    p_end.add_argument("--game", required=True)
    p_end.add_argument("--player", required=True)
    p_end.set_defaults(func=cmd_end_turn)

    p_stat = sub.add_parser("status", help="show current game state")
    p_stat.add_argument("--game", required=True)
    p_stat.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = _open_repo(args.db)
    return args.func(args, repo)


if __name__ == "__main__":
    sys.exit(main())
