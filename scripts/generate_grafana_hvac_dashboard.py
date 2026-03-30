"""One-off generator for Grafana HVAC dashboard JSON."""
import json
from pathlib import Path

DS = {"type": "postgres", "uid": "tsdb-hvac"}
TF = "$__timeFilter"


def pg_target(ref: str, sql: str, fmt: str = "time_series") -> dict:
    return {
        "datasource": DS,
        "editorMode": "code",
        "format": fmt,
        "rawQuery": True,
        "rawSql": sql,
        "refId": ref,
    }


def ts_panel(pid: int, title: str, y: int, x: int, targets: list, w: int = 12, h: int = 8, fc=None) -> dict:
    if fc is None:
        fc = {"defaults": {}, "overrides": []}
    return {
        "datasource": DS,
        "fieldConfig": fc,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": pid,
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "multi", "sort": "none"},
        },
        "targets": targets,
        "title": title,
        "type": "timeseries",
    }


def row_panel(pid: int, title: str, y: int) -> dict:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": pid,
        "panels": [],
        "title": title,
        "type": "row",
    }


def table_panel(pid: int, title: str, y: int, sql: str, h: int = 10) -> dict:
    return {
        "datasource": DS,
        "fieldConfig": {"defaults": {}, "overrides": []},
        "gridPos": {"h": h, "w": 24, "x": 0, "y": y},
        "id": pid,
        "options": {"showHeader": True, "cellHeight": "sm"},
        "targets": [pg_target("A", sql, "table")],
        "title": title,
        "type": "table",
    }


def main() -> None:
    panels: list = []
    pid = 1
    y = 0

    panels.append(row_panel(pid, "Микроклимат цеха", y))
    pid += 1
    y += 1

    panels.append(
        ts_panel(
            pid,
            "Температура, °C",
            y,
            0,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS temp\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'room_temp_c' AND {TF}(time)\nORDER BY time",
                )
            ],
            fc={"defaults": {"unit": "celsius"}, "overrides": []},
        )
    )
    pid += 1

    panels.append(
        ts_panel(
            pid,
            "Влажность, %",
            y,
            12,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS rh\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'room_rh_pct' AND {TF}(time)\nORDER BY time",
                )
            ],
            fc={"defaults": {"unit": "percent"}, "overrides": []},
        )
    )
    pid += 1
    y += 8

    panels.append(
        ts_panel(
            pid,
            "CO₂, ppm",
            y,
            0,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS co2\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'room_co2_ppm' AND {TF}(time)\nORDER BY time",
                )
            ],
        )
    )
    pid += 1

    panels.append(
        ts_panel(
            pid,
            "Скорость воздуха, м/с",
            y,
            12,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS speed\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'room_air_speed_ms' AND {TF}(time)\nORDER BY time",
                )
            ],
        )
    )
    pid += 1
    y += 8

    panels.append(row_panel(pid, "Чиллер KULTEK / R22", y))
    pid += 1
    y += 1

    panels.append(
        ts_panel(
            pid,
            "Давление всас / нагн, бар (абс.)",
            y,
            0,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS p_vs\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_p_suction_bar_abs' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "B",
                    f"SELECT time AS time, value AS p_nd\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_p_discharge_bar_abs' AND {TF}(time)\nORDER BY time",
                ),
            ],
            fc={"defaults": {"unit": "pressure"}, "overrides": []},
        )
    )
    pid += 1

    panels.append(
        ts_panel(
            pid,
            "T нагнетания / T масла, °C",
            y,
            12,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS t_dis\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_t_discharge_c' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "B",
                    f"SELECT time AS time, value AS t_oil\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_t_oil_c' AND {TF}(time)\nORDER BY time",
                ),
            ],
            fc={"defaults": {"unit": "celsius"}, "overrides": []},
        )
    )
    pid += 1
    y += 8

    panels.append(
        ts_panel(
            pid,
            "Испарение °C / перегрев K / дифф. масла бар",
            y,
            0,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS t_evap\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_t_evap_c' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "B",
                    f"SELECT time AS time, value AS sh\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_superheat_k' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "C",
                    f"SELECT time AS time, value AS oil_dp\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'chiller_oil_dp_bar' AND {TF}(time)\nORDER BY time",
                ),
            ],
            w=24,
        )
    )
    pid += 1
    y += 8

    panels.append(row_panel(pid, "Хладоноситель / конденсатор", y))
    pid += 1
    y += 1

    panels.append(
        ts_panel(
            pid,
            "Хладоноситель: T вход·выход, расход м³/ч",
            y,
            0,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS t_in\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'coolant_t_in_c' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "B",
                    f"SELECT time AS time, value AS t_out\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'coolant_t_out_c' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "C",
                    f"SELECT time AS time, value AS flow\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'coolant_flow_m3h' AND {TF}(time)\nORDER BY time",
                ),
            ],
            w=12,
        )
    )
    pid += 1

    panels.append(
        ts_panel(
            pid,
            "Давление контура, МПа / T воды конденсатора",
            y,
            12,
            [
                pg_target(
                    "A",
                    f"SELECT time AS time, value AS p_mpa\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'coolant_pressure_mpa' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "B",
                    f"SELECT time AS time, value AS c_in\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'condenser_t_in_c' AND {TF}(time)\nORDER BY time",
                ),
                pg_target(
                    "C",
                    f"SELECT time AS time, value AS c_out\nFROM sensor_readings\n"
                    f"WHERE sensor_id = 'condenser_t_out_c' AND {TF}(time)\nORDER BY time",
                ),
            ],
            w=12,
        )
    )
    pid += 1
    y += 8

    panels.append(row_panel(pid, "Решения AI", y))
    pid += 1
    y += 1

    sql_ai = f"""SELECT
  created_at AS "Время",
  status AS "Статус",
  COALESCE(ai_response->>'alert_level', '') AS "Уровень",
  COALESCE(ai_response->>'problem', '') AS "Проблема",
  COALESCE(ai_response->>'message', '') AS "Сообщение"
FROM ai_decisions
WHERE {TF}(created_at)
ORDER BY created_at DESC
LIMIT 200"""

    panels.append(table_panel(pid, "Последние решения AI (ai_decisions)", y, sql_ai))
    pid += 1
    y += 10

    panels.append(row_panel(pid, "Алерты", y))
    pid += 1
    y += 1

    sql_alerts = f"""SELECT created_at AS "Время", level AS "Уровень", parameter AS "Параметр",
  value AS "Значение", threshold AS "Порог", message AS "Текст"
FROM alerts
WHERE {TF}(created_at)
ORDER BY created_at DESC
LIMIT 100"""

    panels.append(table_panel(pid, "Таблица alerts (если workflow пишет)", y, sql_alerts, h=8))

    dashboard = {
        "uid": "hvac",
        "title": "HVAC — цех нитроаммофоски",
        "description": "Provisioning: sensor_readings + ai_decisions + alerts",
        "tags": ["timescale", "hvac"],
        "timezone": "Europe/Moscow",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "5s",
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "templating": {"list": []},
        "annotations": {"list": []},
        "editable": True,
        "graphTooltip": 1,
        "links": [],
        "panels": panels,
    }

    root = Path(__file__).resolve().parents[1]
    out = root / "grafana" / "provisioning" / "dashboards" / "hvac.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(panels)} panels)")


if __name__ == "__main__":
    main()
