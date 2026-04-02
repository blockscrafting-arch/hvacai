"""
Минимальный MQTT-издатель снимков hvac/snapshot для проверки стека на сервере.
Интервал и параметры — через переменные окружения (см. docker-compose).

ANOMALY_PROB (0.0–1.0): вероятность впрыска одной случайной аномалии за тик.
По умолчанию 0.20 — каждые ~5 тиков один параметр выходит за пороги.
"""
from __future__ import annotations

import json
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "mosquitto")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "hvac/snapshot")
INTERVAL_SEC = float(os.environ.get("PUBLISH_INTERVAL_SEC", "5"))
ANOMALY_PROB = float(os.environ.get("ANOMALY_PROB", "0.20"))


def _build_nominal_payload() -> dict:
    """Нормальные показания — все параметры в пределах рабочих норм."""
    return {
        "room": {
            "temp_c": 20 + random.uniform(-2, 4),
            "rh_pct": 50 + random.uniform(-10, 20),
            "co2_ppm": 900 + random.randint(-50, 450),   # 850–1350 → всегда normal
            "air_speed_ms": 0.15 + random.uniform(0, 0.15),
        },
        "chiller": {
            "t_evap_c": -7.5 + random.uniform(-0.5, 0.5),
            "p_suction_bar_abs": 3.8 + random.uniform(-0.2, 0.2),
            "p_discharge_bar_abs": 15.0 + random.uniform(-0.5, 0.5),
            "superheat_k": 7 + random.uniform(-1, 3),
            "t_discharge_c": 82 + random.uniform(-5, 15),
            "t_oil_c": 50 + random.uniform(-3, 8),
            "oil_dp_bar": 1.4 + random.uniform(-0.1, 0.1),
        },
        "coolant": {
            "t_in_c": 11 + random.uniform(-1, 2),
            "t_out_c": -2 + random.uniform(-0.5, 0.5),
            "flow_m3h": 200 + random.uniform(-20, 30),
            "pressure_mpa": 1.15 + random.uniform(-0.05, 0.1),
        },
        "condenser": {"t_in_c": 26, "t_out_c": 33},
    }


# ---------------------------------------------------------------------------
# Функции аномалий (каждая переводит один параметр в зону warning или critical)
# ---------------------------------------------------------------------------

def _anom_room_temp_high(p: dict) -> None:
    """t помещения > 26°C (warning) или > 30°C (critical)."""
    p["room"]["temp_c"] = random.uniform(27.0, 33.0)


def _anom_room_temp_low(p: dict) -> None:
    """t помещения < 16°C (warning) или < 14°C (critical)."""
    p["room"]["temp_c"] = random.uniform(11.0, 15.5)


def _anom_room_co2_warning(p: dict) -> None:
    """CO2 ≥ 1400 ppm (warning)."""
    p["room"]["co2_ppm"] = random.randint(1420, 1950)


def _anom_room_co2_critical(p: dict) -> None:
    """CO2 ≥ 2000 ppm (critical)."""
    p["room"]["co2_ppm"] = random.randint(2010, 2400)


def _anom_p_suction_low(p: dict) -> None:
    """Давление всасывания < 2.5 бар (warning) или < 1.5 бар (critical)."""
    p["chiller"]["p_suction_bar_abs"] = random.uniform(0.8, 2.3)


def _anom_t_discharge_high(p: dict) -> None:
    """T нагнетания ≥ 120°C (warning) или ≥ 135°C (critical)."""
    p["chiller"]["t_discharge_c"] = random.uniform(122.0, 145.0)


def _anom_t_oil_high(p: dict) -> None:
    """T масла ≥ 65°C (warning) или ≥ 75°C (critical)."""
    p["chiller"]["t_oil_c"] = random.uniform(67.0, 80.0)


def _anom_oil_dp_low(p: dict) -> None:
    """ΔP масла < 1.1 бар (warning) или < 0.65 бар (critical)."""
    p["chiller"]["oil_dp_bar"] = random.uniform(0.3, 1.05)


def _anom_coolant_tout_low(p: dict) -> None:
    """T вых хладоносителя < −10°C (critical)."""
    p["coolant"]["t_out_c"] = random.uniform(-14.0, -10.5)


def _anom_coolant_pressure_high(p: dict) -> None:
    """Давление хладоносителя > 1.3 МПа (warning)."""
    p["coolant"]["pressure_mpa"] = random.uniform(1.33, 1.60)


def _anom_coolant_flow_low(p: dict) -> None:
    """Расход хладоносителя < 100 м³/ч (warning)."""
    p["coolant"]["flow_m3h"] = random.uniform(40.0, 95.0)


_ANOMALY_FUNCS = [
    _anom_room_temp_high,
    _anom_room_temp_low,
    _anom_room_co2_warning,
    _anom_room_co2_critical,
    _anom_p_suction_low,
    _anom_t_discharge_high,
    _anom_t_oil_high,
    _anom_oil_dp_low,
    _anom_coolant_tout_low,
    _anom_coolant_pressure_high,
    _anom_coolant_flow_low,
]


def inject_anomaly(payload: dict, prob: float = ANOMALY_PROB) -> dict:
    """С вероятностью prob впрыскивает одно случайное отклонение в payload."""
    if random.random() < prob:
        random.choice(_ANOMALY_FUNCS)(payload)
    return payload


def build_payload() -> dict:
    """Снимок с возможной аномалией (вероятность задаётся ANOMALY_PROB)."""
    return inject_anomaly(_build_nominal_payload())


def run() -> None:
    client = mqtt.Client(client_id="hvac-simulator")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()
    try:
        while True:
            payload = build_payload()
            body = json.dumps(payload, ensure_ascii=False)
            res = client.publish(TOPIC, body, qos=0, retain=False)
            res.wait_for_publish(timeout=5.0)
            anomaly_flag = ""
            if any([
                payload["room"]["temp_c"] > 26 or payload["room"]["temp_c"] < 16,
                payload["room"]["co2_ppm"] >= 1400,
                payload["chiller"]["p_suction_bar_abs"] < 2.5,
                payload["chiller"]["t_discharge_c"] >= 120,
                payload["chiller"]["t_oil_c"] >= 65,
                payload["chiller"]["oil_dp_bar"] < 1.1,
                payload["coolant"]["t_out_c"] < -10,
                payload["coolant"]["pressure_mpa"] > 1.3,
                payload["coolant"]["flow_m3h"] < 100,
            ]):
                anomaly_flag = " [ANOMALY]"
            print(f"published {TOPIC} bytes={len(body)}{anomaly_flag}")
            time.sleep(INTERVAL_SEC)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
