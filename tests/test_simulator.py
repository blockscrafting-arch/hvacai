from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator"))
from main import _build_nominal_payload, build_payload, inject_anomaly, _ANOMALY_FUNCS  # noqa: E402


def test_build_payload_structure() -> None:
    p = build_payload()
    assert set(p.keys()) >= {"room", "chiller", "coolant", "condenser"}
    for key in ("temp_c", "rh_pct", "co2_ppm", "air_speed_ms"):
        assert key in p["room"]
    json.dumps(p, ensure_ascii=False)


def test_nominal_payload_stays_in_normal_range() -> None:
    """Номинальный снимок (без аномалий) всегда в безопасных диапазонах."""
    for _ in range(30):
        p = _build_nominal_payload()
        assert 16 <= p["room"]["temp_c"] <= 26, p["room"]["temp_c"]
        assert 800 <= p["room"]["co2_ppm"] <= 1390, p["room"]["co2_ppm"]
        assert 2.5 <= p["chiller"]["p_suction_bar_abs"] <= 6.0
        assert p["chiller"]["t_discharge_c"] < 120
        assert p["chiller"]["t_oil_c"] < 65
        assert p["chiller"]["oil_dp_bar"] >= 1.1
        assert p["coolant"]["t_out_c"] >= -10
        assert p["coolant"]["pressure_mpa"] <= 1.3
        assert p["coolant"]["flow_m3h"] >= 100


def test_inject_anomaly_prob_zero_changes_nothing() -> None:
    """При prob=0 payload не меняется."""
    for _ in range(20):
        p = _build_nominal_payload()
        original_co2 = p["room"]["co2_ppm"]
        result = inject_anomaly(p, prob=0.0)
        assert result["room"]["co2_ppm"] == original_co2


def test_inject_anomaly_prob_one_always_triggers() -> None:
    """При prob=1 хотя бы один параметр гарантированно изменился."""
    triggered = False
    for _ in range(10):
        p = _build_nominal_payload()
        # Сохраняем снимок до аномалии
        snap = json.loads(json.dumps(p))
        inject_anomaly(p, prob=1.0)
        if p != snap:
            triggered = True
            break
    assert triggered, "inject_anomaly(prob=1.0) должна изменить payload"


def test_all_anomaly_funcs_produce_out_of_range_values() -> None:
    """Каждая функция аномалии выводит свой параметр за пороги хотя бы раз из 5."""
    THRESHOLDS = {
        "room.temp_c": (lambda p: p["room"]["temp_c"] < 16 or p["room"]["temp_c"] > 26),
        "room.co2_ppm": (lambda p: p["room"]["co2_ppm"] >= 1400),
        "chiller.p_suction": (lambda p: p["chiller"]["p_suction_bar_abs"] < 2.5),
        "chiller.t_discharge": (lambda p: p["chiller"]["t_discharge_c"] >= 120),
        "chiller.t_oil": (lambda p: p["chiller"]["t_oil_c"] >= 65),
        "chiller.oil_dp": (lambda p: p["chiller"]["oil_dp_bar"] < 1.1),
        "coolant.t_out": (lambda p: p["coolant"]["t_out_c"] < -10),
        "coolant.pressure": (lambda p: p["coolant"]["pressure_mpa"] > 1.3),
        "coolant.flow": (lambda p: p["coolant"]["flow_m3h"] < 100),
    }
    for fn in _ANOMALY_FUNCS:
        triggered = False
        for _ in range(5):
            p = _build_nominal_payload()
            fn(p)
            if any(check(p) for check in THRESHOLDS.values()):
                triggered = True
                break
        assert triggered, f"{fn.__name__} не вывела ни одного параметра за порог"


def test_build_payload_serialisable() -> None:
    """Payload всегда сериализуется в JSON без ошибок."""
    for _ in range(20):
        p = build_payload()
        body = json.dumps(p, ensure_ascii=False)
        assert len(body) > 50
