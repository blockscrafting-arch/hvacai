-- TimescaleDB / PostgreSQL 16 — схема из плана диплома (hvac_ai_diploma_system)
-- Перед apply: создайте БД и пользователя; расширение timescaledb — в образе timescale/timescaledb

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Показания датчиков (hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
  time         TIMESTAMPTZ NOT NULL,
  sensor_id    TEXT NOT NULL,
  sensor_type  TEXT NOT NULL,
  value        DOUBLE PRECISION NOT NULL,
  unit         TEXT NOT NULL,
  location     TEXT DEFAULT 'workshop_1',
  equipment    TEXT
);

SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');

CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_time ON sensor_readings (sensor_id, time DESC);

-- Retention policy: автоудаление данных старше 90 дней (TimescaleDB background worker)
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days', if_not_exists => TRUE);

-- Решения AI-агента
CREATE TABLE IF NOT EXISTS ai_decisions (
  id           SERIAL PRIMARY KEY,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  input_data   JSONB NOT NULL,
  ai_response  JSONB NOT NULL,
  status       TEXT NOT NULL,
  model_used   TEXT DEFAULT 'gpt-4o',
  tokens_used  INTEGER,
  latency_ms   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ai_decisions_created ON ai_decisions (created_at DESC);

-- Управляющие команды (опционально для расширения workflow)
CREATE TABLE IF NOT EXISTS control_commands (
  id           SERIAL PRIMARY KEY,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  target       TEXT NOT NULL,
  command      JSONB NOT NULL,
  source       TEXT DEFAULT 'ai_agent',
  executed     BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS alerts (
  id           SERIAL PRIMARY KEY,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  level        TEXT NOT NULL,
  parameter    TEXT NOT NULL,
  value        DOUBLE PRECISION,
  threshold    DOUBLE PRECISION,
  message      TEXT NOT NULL,
  sent_via     TEXT[],
  acknowledged BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS equipment_config (
  id           SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  manufacturer TEXT,
  refrigerant  TEXT,
  cooling_capacity_kw DOUBLE PRECISION,
  parameters   JSONB
);
