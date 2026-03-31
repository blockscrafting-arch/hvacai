from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator"))
from main import build_payload  # noqa: E402


def test_build_payload_structure() -> None:
    p = build_payload()
    assert set(p.keys()) >= {"room", "chiller", "coolant", "condenser"}
    for key in ("temp_c", "rh_pct", "co2_ppm", "air_speed_ms"):
        assert key in p["room"]
    json.dumps(p, ensure_ascii=False)


def test_build_payload_numeric_ranges() -> None:
    for _ in range(20):
        p = build_payload()
        assert 10 <= p["room"]["temp_c"] <= 40
        assert 800 <= p["room"]["co2_ppm"] <= 1600
        assert -10 <= p["coolant"]["t_out_c"] <= 5
