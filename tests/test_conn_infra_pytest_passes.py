import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
@pytest.mark.skipif(
    os.environ.get("TCG_IN_CONTAINER") == "1",
    reason="prevents recursive docker-in-docker when run inside the image",
)
def test_conn_infra_001_4_s1_pytest_exits_zero_inside_container():
    # GIVEN the image is built and deps installed (prior INFRA scenarios)
    project_root = Path(__file__).resolve().parent.parent
    assert (project_root / "Dockerfile").is_file()

    # WHEN the full pytest suite runs inside the container (excluding the infra
    # tests themselves, which shell out to docker and are host-only)
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-e",
            "TCG_IN_CONTAINER=1",
            "tcg-game",
            "pytest",
            "tests/",
            "--ignore-glob=tests/test_conn_infra_*.py",
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
    )

    # THEN the process exits 0 and output shows tests ran
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert " passed" in result.stdout
