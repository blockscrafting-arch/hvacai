from __future__ import annotations

import json
from pathlib import Path


def _load_workflow(repo_root: Path) -> dict:
    path = repo_root / "n8n" / "workflows" / "hvac-ai-kultek-controller.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_workflow_json_and_ai_pipeline(repo_root: Path) -> None:
    w = _load_workflow(repo_root)
    by_name = {n["name"]: n for n in w["nodes"]}

    assert "К AI только при отклонении" in by_name
    assert "Окно 120 сек для AI" in by_name
    assert "AI Agent HVAC" in by_name

    parse = by_name["Разбор MQTT + пороги"]
    assert "function evaluateRuleSeverity" in parse["parameters"]["jsCode"]
    assert "ruleEval.ruleSeverity" in parse["parameters"]["jsCode"]

    throttle = by_name["Окно 120 сек для AI"]
    assert "120000" in throttle["parameters"]["jsCode"]

    gate = by_name["К AI только при отклонении"]
    assert "ruleSeverity" in gate["parameters"]["jsCode"]

    openai = by_name["OpenAI Chat Model"]
    assert openai["parameters"]["model"]["value"] == "gpt-4o-mini"

    con = w["connections"]
    assert "К AI только при отклонении" in con
    assert con["К AI только при отклонении"]["main"][0][0]["node"] == "Окно 120 сек для AI"
    targets_from_parse = {e["node"] for e in con["Разбор MQTT + пороги"]["main"][0]}
    assert targets_from_parse == {"Развернуть сенсоры в строки БД", "К AI только при отклонении"}


def test_workflow_pg_ai_decisions_model_string(repo_root: Path) -> None:
    w = _load_workflow(repo_root)
    pg = next(n for n in w["nodes"] if n.get("name") == "PostgreSQL ai_decisions")
    qr = pg["parameters"]["options"]["queryReplacement"]
    assert "gpt-4o-mini" in qr
    assert "'gpt-4o'" not in qr  # не оставляем старое имя модели отдельным токеном
