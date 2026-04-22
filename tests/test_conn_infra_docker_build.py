import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_conn_infra_001_1_s1_docker_image_builds_from_project_root():
    # GIVEN a Dockerfile at the project root targeting Python 3.12
    project_root = Path(__file__).resolve().parent.parent
    dockerfile = project_root / "Dockerfile"
    assert dockerfile.is_file(), "Dockerfile must exist at project root"
    assert "python:3.12" in dockerfile.read_text(), "Dockerfile must target Python 3.12"

    # WHEN docker build -t tcg-game . is executed
    build = subprocess.run(
        ["docker", "build", "-t", "tcg-game", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    # THEN the build completes with exit code 0
    assert build.returncode == 0, f"docker build failed:\n{build.stderr}"

    # AND docker images tcg-game lists the image
    images = subprocess.run(
        ["docker", "images", "-q", "tcg-game"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert images.stdout.strip(), "docker images tcg-game should list the image"
