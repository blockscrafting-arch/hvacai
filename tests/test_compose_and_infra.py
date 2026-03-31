from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW_NAME = "hvac-ai-kultek-controller.json"
EXPECTED_SERVICES = {
    "timescaledb",
    "mosquitto",
    "n8n",
    "grafana",
    "caddy",
    "simulator",
}


def test_docker_compose_parse(repo_root: Path) -> None:
    raw = (repo_root / "docker-compose.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    names = set(data.get("services", {}).keys())
    assert EXPECTED_SERVICES <= names
    sim = data["services"]["simulator"]["environment"]
    assert sim["MQTT_TOPIC"] == "hvac/snapshot"
    assert sim["PUBLISH_INTERVAL_SEC"] == "30"
    n8n = data["services"]["n8n"]["environment"]
    assert n8n.get("N8N_BLOCK_ENV_ACCESS_IN_NODE") == "false"


@pytest.mark.skipif(not shutil.which("docker"), reason="Docker CLI not installed")
def test_docker_compose_config_valid(repo_root: Path) -> None:
    # Обязательные подстановки из compose (? : ) без реального .env
    env = {
        **os.environ,
        "POSTGRES_PASSWORD": "pytest-compose-check",
        "N8N_ENCRYPTION_KEY": "a" * 64,
        "GRAFANA_ADMIN_PASSWORD": "pytest-grafana-check",
    }
    r = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr


def test_mosquitto_config(repo_root: Path) -> None:
    txt = (repo_root / "mosquitto" / "config" / "mosquitto.conf").read_text(encoding="utf-8")
    assert "listener 1883" in txt
    assert "allow_anonymous true" in txt


def test_caddyfile_reverse_proxies(repo_root: Path) -> None:
    txt = (repo_root / "caddy" / "Caddyfile").read_text(encoding="utf-8")
    assert "reverse_proxy n8n:5678" in txt
    assert "reverse_proxy grafana:3000" in txt
