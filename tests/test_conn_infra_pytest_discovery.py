import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_conn_infra_001_3_s1_pytest_collects_tests_inside_container():
    # GIVEN test files live under tests/ and pyproject sets pythonpath=src
    project_root = Path(__file__).resolve().parent.parent
    assert (project_root / "tests").is_dir()
    pyproject = (project_root / "pyproject.toml").read_text()
    assert 'pythonpath = ["src"]' in pyproject

    # WHEN pytest --collect-only runs inside the container
    result = subprocess.run(
        ["docker", "run", "--rm", "tcg-game", "pytest", "--collect-only"],
        capture_output=True,
        text=True,
    )

    # THEN collection succeeds with no import errors
    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "ImportError" not in result.stdout
    assert "ImportError" not in result.stderr
    # AND at least one test is collected
    assert "<Function" in result.stdout or "test_" in result.stdout
