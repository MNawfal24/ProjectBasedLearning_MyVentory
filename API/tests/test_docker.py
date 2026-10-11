"""Docker build and container startup test.

Heavy by nature, so it only runs when explicitly requested::

    MYVENTORY_DOCKER_TEST=1 pytest -m docker -v

Builds the image with ``API/Dockerfile`` and the repository root as build context
(needed so ``ML/artifacts`` lands in the image), starts the container, then
checks the health endpoint and the Swagger schema served from inside it.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
IMAGE_TAG = "myventory-api:test"
CONTAINER_NAME = "myventory-api-test"
HOST_PORT = 8123
BASE_URL = f"http://127.0.0.1:{HOST_PORT}"

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        os.environ.get("MYVENTORY_DOCKER_TEST") != "1",
        reason="set MYVENTORY_DOCKER_TEST=1 untuk menjalankan uji Docker",
    ),
]


def run(command: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)


def wait_for(url: str, attempts: int = 60) -> int:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310 - fixed localhost URL
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except Exception as exc:  # noqa: BLE001 - container still starting
            last_error = exc
            time.sleep(2)
    raise AssertionError(f"endpoint {url} tidak merespons: {last_error}")


@pytest.fixture(scope="module")
def container():
    build = run(["docker", "build", "-f", "API/Dockerfile", "-t", IMAGE_TAG, "."])
    assert build.returncode == 0, f"docker build gagal:\n{build.stdout}\n{build.stderr}"
    run(["docker", "rm", "-f", CONTAINER_NAME])
    start = run(["docker", "run", "-d", "--name", CONTAINER_NAME, "-p", f"{HOST_PORT}:8000", IMAGE_TAG])
    assert start.returncode == 0, f"docker run gagal:\n{start.stdout}\n{start.stderr}"
    try:
        yield
    finally:
        logs = run(["docker", "logs", CONTAINER_NAME])
        run(["docker", "rm", "-f", CONTAINER_NAME])
        print(logs.stdout[-4000:])


def test_container_serves_health_and_readiness(container):
    assert wait_for(f"{BASE_URL}/api/v1/health") == 200
    with urllib.request.urlopen(f"{BASE_URL}/api/v1/ready", timeout=10) as response:  # noqa: S310
        body = json.loads(response.read())
    assert body["status"] in ("ready", "not_ready")
    assert len(body["models"]) == 5


def test_container_serves_swagger_and_openapi(container):
    assert wait_for(f"{BASE_URL}/docs") == 200
    with urllib.request.urlopen(f"{BASE_URL}/openapi.json", timeout=10) as response:  # noqa: S310
        schema = json.loads(response.read())
    assert "/api/v1/sales-forecast" in schema["paths"]


def test_container_predicts_with_bundled_artifacts(container):
    """The image must carry the model artefacts and load all five of them."""
    with urllib.request.urlopen(f"{BASE_URL}/api/v1/ready", timeout=10) as response:  # noqa: S310
        ready = json.loads(response.read())
    assert sorted(ready["ready_models"]) == [
        "demand_forecast",
        "peak_hour",
        "sales_forecast",
        "segmentation",
        "stock_prediction",
    ], ready

    request = urllib.request.Request(  # noqa: S310 - fixed localhost URL
        f"{BASE_URL}/api/v1/sales-forecast",
        data=json.dumps({"outlet": "SHOP001", "horizon_days": 3}).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        body = json.loads(response.read())
    assert body["model_version"]
    assert len(body["predictions"]) == 3
    assert all(point["predicted_net_sales"] > 0 for point in body["predictions"])


def test_container_runs_as_non_root_without_baked_secrets(container):
    user = run(["docker", "exec", CONTAINER_NAME, "id", "-u"])
    assert user.returncode == 0
    assert user.stdout.strip() != "0", "container berjalan sebagai root"

    env = run(["docker", "exec", CONTAINER_NAME, "env"])
    leaked = [
        line
        for line in env.stdout.splitlines()
        if any(marker in line.upper() for marker in ("SECRET", "PASSWORD", "API_KEY", "TOKEN="))
    ]
    assert leaked == [], f"environment variable sensitif ditemukan: {leaked}"

    # runtime config must come from environment variables, not from baked files
    config = run(["docker", "exec", CONTAINER_NAME, "python", "-c", "from app.config import settings; print(settings.artifacts_root)"])
    assert config.returncode == 0, config.stderr
    assert config.stdout.strip() == "/app/ML/artifacts"
