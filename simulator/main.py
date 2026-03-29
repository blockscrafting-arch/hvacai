"""
Минимальный MQTT-издатель снимков hvac/snapshot для проверки стека на сервере.
Интервал и параметры — через переменные окружения (см. docker-compose).
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


def build_payload() -> dict:
    """Слегка «шумящий» снимок в формате, ожидаемом n8n workflow."""
    co2 = 900 + random.randint(-50, 600)
    return {
        "room": {
            "temp_c": 20 + random.uniform(-2, 4),
            "rh_pct": 50 + random.uniform(-10, 20),
            "co2_ppm": co2,
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
            print(f"published {TOPIC} bytes={len(body)}")
            time.sleep(INTERVAL_SEC)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
