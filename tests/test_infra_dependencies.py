import shutil
import subprocess

import pytest

IMAGE = "tcg-game"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.mark.skipif(not _docker_available(), reason="docker not available in this env")
def test_conn_infra_001_2_s1_declared_packages_importable_inside_container():
    # GIVEN the Docker image is built with dependencies installed
    # WHEN we run `python -c "import pytest; import domain.game"` inside the container
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            IMAGE,
            "python",
            "-c",
            "import pytest; import domain.game",
        ],
        capture_output=True,
        text=True,
    )

    # THEN the command exits with code 0 and no ImportError is printed
    assert result.returncode == 0, result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "ImportError" not in result.stderr
