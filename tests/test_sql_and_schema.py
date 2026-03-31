from __future__ import annotations

import re
from pathlib import Path


def test_init_sql_expected_objects(repo_root: Path) -> None:
    sql = (repo_root / "sql" / "init.sql").read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS timescaledb" in sql
    assert re.search(r"CREATE TABLE IF NOT EXISTS sensor_readings", sql)
    assert "create_hypertable('sensor_readings'" in sql
    assert "add_retention_policy('sensor_readings'" in sql
    assert "INTERVAL '90 days'" in sql
    assert "CREATE TABLE IF NOT EXISTS ai_decisions" in sql
    assert "CREATE TABLE IF NOT EXISTS alerts" in sql
