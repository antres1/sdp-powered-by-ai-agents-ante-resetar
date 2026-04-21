import shutil
import subprocess

import pytest

IMAGE = "tcg-game"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.mark.skipif(not _docker_available(), reason="docker not available in this env")
def test_conn_infra_001_3_s1_pytest_collects_tests_without_import_errors():
    # GIVEN test files under tests/ and pyproject.toml sets pythonpath to src
    # WHEN `docker run --rm tcg-game pytest --collect-only` is executed
    result = subprocess.run(
        ["docker", "run", "--rm", IMAGE, "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
    )

    # THEN pytest collects tests, exits 0, no ImportError in output
    assert result.returncode == 0, result.stderr + result.stdout
    assert "ImportError" not in result.stdout
    assert "ImportError" not in result.stderr
    # collected items are listed (at least one of the existing play-card tests)
    assert "test_play_card" in result.stdout
