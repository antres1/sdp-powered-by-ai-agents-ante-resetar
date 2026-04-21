import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE = "tcg-game"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.mark.skipif(not _docker_available(), reason="docker not available in this env")
def test_conn_infra_001_1_s1_docker_image_builds_from_project_root():
    # GIVEN a Dockerfile at the project root targeting Python 3.12
    assert (PROJECT_ROOT / "Dockerfile").is_file()

    # WHEN `docker build -t tcg-game .` is executed
    build = subprocess.run(
        ["docker", "build", "-t", IMAGE, "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    # THEN the build completes with exit code 0
    assert build.returncode == 0, build.stderr

    # AND `docker images tcg-game` lists the image
    listed = subprocess.run(
        ["docker", "images", "-q", IMAGE],
        capture_output=True,
        text=True,
        check=True,
    )
    assert listed.stdout.strip() != ""
