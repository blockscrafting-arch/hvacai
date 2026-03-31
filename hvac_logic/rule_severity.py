"""
Правила ветвления AI (зеркало n8n «Разбор MQTT + пороги» + evaluateRuleSeverity).
При изменении порогов в workflow — синхронизировать этот файл и patch-workflow скрипт.
"""
from __future__ import annotations

from typing import Any, TypedDict


class RuleEval(TypedDict):
    ruleSeverity: str
    ruleIssues: list[str]
    ruleSummary: str


# Совпадает с THRESHOLDS в n8n Code node
THRESHOLDS: dict[str, Any] = {
    "room": {
        "temp_critical_below": 14,
        "temp_critical_above": 30,
        "temp_warning_below": 16,
        "temp_warning_above": 26,
        "rh_critical_below": 10,
        "rh_critical_above": 85,
        "rh_warning_below": 15,
        "rh_warning_above": 75,
        "co2_ppm_critical": 2000,
        "co2_ppm_warning": 1400,
        "air_speed_ms_warning_above": 0.5,
    },
    "chiller_r22": {
        "t_evap_c_range": [-20, 5],
        "t_evap_warning_below": -15,
        "t_evap_warning_above": 2,
        "p_suction_bar_abs_range": [1.0, 8.0],
        "p_suction_critical_below": 1.5,
        "p_suction_warn_below": 2.5,
        "p_discharge_bar_abs_range": [8.0, 25.0],
        "p_discharge_warn_above": 20,
        "p_discharge_critical_above": 25,
        "superheat_crit_below": 1,
        "superheat_crit_above": 20,
        "superheat_warn_below": 3,
        "superheat_warn_above": 15,
        "t_discharge_critical_c": 135,
        "t_discharge_warn_c": 120,
        "t_oil_critical_c": 75,
        "t_oil_warn_c": 65,
        "oil_dp_critical_below": 0.65,
        "oil_dp_warn_below": 1.1,
    },
    "coolant_nh3_20pct": {
        "t_out_critical_below_c": -10,
        "t_out_c_range": [-10, 15],
        "t_in_c_range": [-5, 20],
        "flow_warn_below": 100,
        "pressure_warn_above_mpa": 1.3,
    },
    "condenser_water": {"t_out_c_nominal": 33},
}


def evaluate_rule_severity(payload: dict[str, Any], h: dict[str, Any] | None = None) -> RuleEval:
    h = h or THRESHOLDS
    sev = "normal"
    issues: list[str] = []

    def bump(level: str, msg: str) -> None:
        nonlocal sev
        issues.append(msg)
        if level == "critical":
            sev = "critical"
        elif level == "warning" and sev != "critical":
            sev = "warning"

    room = payload.get("room") or {}
    ch = payload.get("chiller") or {}
    nh3 = payload.get("coolant") or {}
    cond = payload.get("condenser") or {}
    r = h["room"]
    c = h["chiller_r22"]
    n = h["coolant_nh3_20pct"]

    if room.get("temp_c") is not None:
        t = float(room["temp_c"])
        if t < r["temp_critical_below"] or t > r["temp_critical_above"]:
            bump("critical", f"t помещения {t}°C")
        elif t < r["temp_warning_below"] or t > r["temp_warning_above"]:
            bump("warning", f"t помещения {t}°C вне комфорта")

    if room.get("rh_pct") is not None:
        rh = float(room["rh_pct"])
        if rh < r["rh_critical_below"] or rh > r["rh_critical_above"]:
            bump("critical", f"RH {rh}%")
        elif rh < r["rh_warning_below"] or rh > r["rh_warning_above"]:
            bump("warning", f"RH {rh}%")

    if room.get("co2_ppm") is not None:
        co2 = float(room["co2_ppm"])
        if co2 >= r["co2_ppm_critical"]:
            bump("critical", f"CO2 {co2} ppm")
        elif co2 >= r["co2_ppm_warning"]:
            bump("warning", f"CO2 {co2} ppm")

    if room.get("air_speed_ms") is not None:
        v = float(room["air_speed_ms"])
        if v > r["air_speed_ms_warning_above"]:
            bump("warning", f"скорость воздуха {v} м/с")

    if ch.get("t_evap_c") is not None:
        te = float(ch["t_evap_c"])
        lo, hi = c["t_evap_c_range"]
        if te < lo or te > hi:
            bump("critical", f"T исп {te}°C вне диапазона")
        elif te < c["t_evap_warning_below"] or te > c["t_evap_warning_above"]:
            bump("warning", f"T исп {te}°C")

    if ch.get("p_suction_bar_abs") is not None:
        p = float(ch["p_suction_bar_abs"])
        lo, hi = c["p_suction_bar_abs_range"]
        if p < lo or p > hi:
            bump("critical", f"P всас {p} бар вне диапазона")
        elif p < c["p_suction_critical_below"]:
            bump("critical", f"P всас {p} бар")
        elif p < c["p_suction_warn_below"]:
            bump("warning", f"P всас {p} бар")

    if ch.get("p_discharge_bar_abs") is not None:
        p = float(ch["p_discharge_bar_abs"])
        lo, hi = c["p_discharge_bar_abs_range"]
        if p < lo or p > hi:
            bump("critical", f"P нагн {p} бар вне диапазона")
        elif p >= c["p_discharge_critical_above"]:
            bump("critical", f"P нагн {p} бар")
        elif p >= c["p_discharge_warn_above"]:
            bump("warning", f"P нагн {p} бар")

    if ch.get("superheat_k") is not None:
        sh = float(ch["superheat_k"])
        if sh < c["superheat_crit_below"] or sh > c["superheat_crit_above"]:
            bump("critical", f"перегрев {sh} K")
        elif sh < c["superheat_warn_below"] or sh > c["superheat_warn_above"]:
            bump("warning", f"перегрев {sh} K")

    if ch.get("t_discharge_c") is not None:
        td = float(ch["t_discharge_c"])
        if td >= c["t_discharge_critical_c"]:
            bump("critical", f"T нагн {td}°C")
        elif td >= c["t_discharge_warn_c"]:
            bump("warning", f"T нагн {td}°C")

    if ch.get("t_oil_c") is not None:
        to = float(ch["t_oil_c"])
        if to >= c["t_oil_critical_c"]:
            bump("critical", f"T масла {to}°C")
        elif to >= c["t_oil_warn_c"]:
            bump("warning", f"T масла {to}°C")

    if ch.get("oil_dp_bar") is not None:
        od = float(ch["oil_dp_bar"])
        if od < c["oil_dp_critical_below"]:
            bump("critical", f"ΔP масла {od} бар")
        elif od < c["oil_dp_warn_below"]:
            bump("warning", f"ΔP масла {od} бар")

    tin = nh3.get("t_in_c", nh3.get("coolant_t_in"))
    tout = nh3.get("t_out_c", nh3.get("coolant_t_out"))
    flow = nh3.get("flow_m3h", nh3.get("coolant_flow"))
    press = nh3.get("pressure_mpa", nh3.get("coolant_pressure"))

    if tout is not None:
        t = float(tout)
        if t < n["t_out_critical_below_c"]:
            bump("critical", f"T вых хладоносителя {t}°C")
        else:
            lo, hi = n["t_out_c_range"]
            if t < lo or t > hi:
                bump("warning", f"T вых хладоносителя {t}°C")

    if tin is not None:
        t = float(tin)
        lo, hi = n["t_in_c_range"]
        if t < lo or t > hi:
            bump("warning", f"T вх хладоносителя {t}°C")

    if flow is not None:
        f = float(flow)
        if f < n["flow_warn_below"]:
            bump("warning", f"расход {f} м³/ч")

    if press is not None:
        pr = float(press)
        if pr > n["pressure_warn_above_mpa"]:
            bump("warning", f"давление {pr} МПа")

    if cond.get("t_out_c") is not None and h.get("condenser_water"):
        t = float(cond["t_out_c"])
        nom = h["condenser_water"]["t_out_c_nominal"]
        if t > nom + 5:
            bump("warning", f"T вых конденсатора {t}°C")

    return {
        "ruleSeverity": sev,
        "ruleIssues": issues,
        "ruleSummary": "; ".join(issues) if issues else "в пределах правил",
    }
