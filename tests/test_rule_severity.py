"""Golden cases для evaluate_rule_severity (паритет с n8n)."""
from __future__ import annotations

import copy

import pytest

from hvac_logic.rule_severity import THRESHOLDS, evaluate_rule_severity


def _nominal_payload() -> dict:
    return {
        "room": {"temp_c": 21, "rh_pct": 55, "co2_ppm": 800, "air_speed_ms": 0.2},
        "chiller": {
            "t_evap_c": -7.5,
            "p_suction_bar_abs": 3.87,
            "p_discharge_bar_abs": 15.3,
            "superheat_k": 7,
            "t_discharge_c": 85,
            "t_oil_c": 50,
            "oil_dp_bar": 1.4,
        },
        "coolant": {"t_in_c": 12, "t_out_c": -2, "flow_m3h": 200, "pressure_mpa": 1.15},
        "condenser": {"t_in_c": 26, "t_out_c": 33},
    }


def test_nominal_is_normal() -> None:
    r = evaluate_rule_severity(_nominal_payload())
    assert r["ruleSeverity"] == "normal"
    assert r["ruleIssues"] == []


@pytest.mark.parametrize(
    "mutation, expected_min",
    [
        (lambda p: p["room"].update({"temp_c": 31}), "critical"),
        (lambda p: p["room"].update({"temp_c": 15}), "warning"),  # ниже temp_warning_below (16)
        (lambda p: p["room"].update({"co2_ppm": 1450}), "warning"),
        (lambda p: p["room"].update({"co2_ppm": 2100}), "critical"),
        (lambda p: p["coolant"].update({"t_out_c": -11}), "critical"),
        (lambda p: p["chiller"].update({"p_suction_bar_abs": 0.5}), "critical"),
    ],
)
def test_deviations_raise_severity(
    mutation: callable, expected_min: str
) -> None:
    p = _nominal_payload()
    mutation(p)
    r = evaluate_rule_severity(p)
    order = {"normal": 0, "warning": 1, "critical": 2}
    assert order[r["ruleSeverity"]] >= order[expected_min]


def test_coolant_alternate_keys() -> None:
    p = copy.deepcopy(_nominal_payload())
    del p["coolant"]["t_out_c"]
    p["coolant"]["coolant_t_out"] = -11
    assert evaluate_rule_severity(p)["ruleSeverity"] == "critical"
