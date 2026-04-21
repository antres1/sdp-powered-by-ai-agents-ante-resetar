import shutil
import subprocess

import pytest

IMAGE = "tcg-game"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.mark.skipif(not _docker_available(), reason="docker not available in this env")
def test_conn_infra_001_4_s1_pytest_exits_zero_inside_container():
    # GIVEN the image is built and dependencies are installed
    # WHEN `docker run --rm tcg-game pytest` is executed
    # We ignore the in-container infra tests (they can't run docker from inside docker).
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            IMAGE,
            "pytest",
            "tests/",
            "--ignore-glob=tests/test_infra_*.py",
            "-v",
        ],
        capture_output=True,
        text=True,
    )

    # THEN all tests pass and the process exits with code 0
    assert result.returncode == 0, result.stderr + result.stdout
    assert "failed" not in result.stdout.lower() or " 0 failed" in result.stdout.lower()
