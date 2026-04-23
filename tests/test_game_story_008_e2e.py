"""
GAME-STORY-008: Shared domain code packaged as a Python package.
"""

import ast
from pathlib import Path


def test_game_story_008_s1_domain_functions_are_importable():
    # GIVEN the domain package exists under src/domain/
    # WHEN the domain functions are imported
    # THEN no ImportError is raised and all three functions are callable
    from domain.game import end_turn, is_game_over, play_card
    from domain.models import GameState, RuleViolationError

    assert callable(play_card)
    assert callable(end_turn)
    assert callable(is_game_over)
    assert GameState is not None
    assert RuleViolationError is not None


INFRA_MODULES = {"sqlite3", "websockets", "fastapi", "flask", "aiohttp", "boto3"}


def _collect_imports(path: Path) -> set[str]:
    """Return top-level module names imported in a Python source file."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_game_story_008_s2_domain_has_zero_infrastructure_imports():
    # GIVEN the domain package source files under src/domain/
    domain_dir = Path("src/domain")
    assert domain_dir.is_dir(), "src/domain/ must exist"

    py_files = list(domain_dir.glob("*.py"))
    assert py_files, "src/domain/ must contain at least one .py file"

    # WHEN each file is inspected for infrastructure imports
    violations: list[str] = []
    for py_file in py_files:
        imports = _collect_imports(py_file)
        found = imports & INFRA_MODULES
        for name in found:
            violations.append(f"{py_file}: imports '{name}'")

    # THEN no infrastructure imports are found
    assert not violations, "Infrastructure imports found in domain:\n" + "\n".join(
        violations
    )
