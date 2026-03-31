"""Общая логика HVAC (калибровка с n8n evaluateRuleSeverity)."""

from .rule_severity import THRESHOLDS, evaluate_rule_severity

__all__ = ["THRESHOLDS", "evaluate_rule_severity"]
