from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_grafana_hvac_dashboard import build_dashboard  # noqa: E402


def test_provisioned_hvac_dashboard_has_uid(repo_root: Path) -> None:
    p = repo_root / "grafana" / "provisioning" / "dashboards" / "hvac.json"
    dash = json.loads(p.read_text(encoding="utf-8"))
    assert dash["uid"] == "hvac"
    assert dash["timezone"] == "Europe/Moscow"
    assert len(dash["panels"]) >= 3


def test_datasource_provisioning(repo_root: Path) -> None:
    yml_path = repo_root / "grafana" / "provisioning" / "datasources" / "timescale.yml"
    doc = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
    ds = doc["datasources"][0]
    assert ds["uid"] == "tsdb-hvac"
    assert ds["type"] == "postgres"
    assert ds["jsonData"].get("database") == "hvac"


def test_build_dashboard_matches_committed_schema(repo_root: Path) -> None:
    """Генератор даёт тот же uid и согласованное число панелей с файлом в репо."""
    built = build_dashboard()
    on_disk = json.loads(
        (repo_root / "grafana" / "provisioning" / "dashboards" / "hvac.json").read_text(
            encoding="utf-8"
        )
    )
    assert built["uid"] == on_disk["uid"]
    assert len(built["panels"]) == len(on_disk["panels"])
