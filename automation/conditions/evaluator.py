from typing import Any
from automation.conditions.operators import OPERATORS
from automation.conditions.rules import Rule


def resolve_field_path(context: dict[str, Any], path: str) -> Any:
    """Traverses dot notation (e.g. 'vision.confidence') into nested dicts."""
    if not path or not isinstance(context, dict):
        return None
    parts = path.split(".")
    curr = context
    for p in parts:
        if isinstance(curr, dict):
            curr = curr.get(p)
        elif hasattr(curr, p):
            curr = getattr(curr, p)
        else:
            return None
    return curr


class ConditionEvaluator:
    """Evaluates business rules against execution context without dynamic code execution."""

    def evaluate(self, rule: Rule, context: dict) -> bool:
        val = resolve_field_path(context, rule.field)
        op_key = rule.operator.strip().lower()
        op_fn = OPERATORS.get(op_key) or OPERATORS.get(rule.operator)
        if not op_fn:
            return False
        return op_fn(val, rule.expected_value)
