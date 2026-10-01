from app.automation.conditions.evaluator import ConditionEvaluator
from app.automation.conditions.rules import Rule


def test_condition_evaluation():
    evaluator = ConditionEvaluator()
    rule = Rule(field="amount", operator=">", expected_value=1000)
    assert evaluator.evaluate(rule, {"amount": 5000}) is True
    assert evaluator.evaluate(rule, {"amount": 200}) is False
