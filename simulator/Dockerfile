FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV MQTT_HOST=mosquitto \
    MQTT_PORT=1883 \
    MQTT_TOPIC=hvac/snapshot \
    PUBLISH_INTERVAL_SEC=5

CMD ["python", "-u", "main.py"]
