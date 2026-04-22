import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_conn_infra_001_2_s1_declared_packages_importable_inside_container():
    # GIVEN requirements.txt lists deps and the Dockerfile runs pip install
    project_root = Path(__file__).resolve().parent.parent
    assert (project_root / "requirements.txt").is_file()
    assert "pip install" in (project_root / "Dockerfile").read_text()

    # WHEN the container runs a smoke import for pytest and the domain package
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "tcg-game",
            "python",
            "-c",
            "import pytest; import domain.game",
        ],
        capture_output=True,
        text=True,
    )

    # THEN the command exits 0 with no import errors
    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "ModuleNotFoundError" not in result.stderr
    assert "ImportError" not in result.stderr
