from automation.conditions.operators import OPERATORS
from automation.conditions.rules import Rule

class ConditionEvaluator:
    def evaluate(self, rule: Rule, context: dict) -> bool:
        val = context.get(rule.field)
        op_fn = OPERATORS.get(rule.operator)
        if not op_fn:
            return False
        return op_fn(val, rule.expected_value)
