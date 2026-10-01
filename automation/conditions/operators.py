"""
OmniAgent AI — Automation Condition Operators
Deterministic evaluation functions without using eval() or dynamic code execution.
"""

def safe_contains(a, b) -> bool:
    if a is None:
        return False
    try:
        return b in a
    except (TypeError, ValueError):
        return str(b) in str(a)

def safe_not_contains(a, b) -> bool:
    return not safe_contains(a, b)

def safe_gt(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) > float(b)
    except (ValueError, TypeError):
        return str(a) > str(b)

def safe_lt(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) < float(b)
    except (ValueError, TypeError):
        return str(a) < str(b)

def safe_gte(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) >= float(b)
    except (ValueError, TypeError):
        return str(a) >= str(b)

def safe_lte(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) <= float(b)
    except (ValueError, TypeError):
        return str(a) <= str(b)

OPERATORS = {
    "==": lambda a, b: a == b,
    "equals": lambda a, b: a == b,
    "eq": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "not_equals": lambda a, b: a != b,
    "ne": lambda a, b: a != b,
    ">": safe_gt,
    "greater_than": safe_gt,
    "gt": safe_gt,
    "<": safe_lt,
    "less_than": safe_lt,
    "lt": safe_lt,
    ">=": safe_gte,
    "greater_than_or_equal": safe_gte,
    "gte": safe_gte,
    "<=": safe_lte,
    "less_than_or_equal": safe_lte,
    "lte": safe_lte,
    "contains": safe_contains,
    "not_contains": safe_not_contains,
    "exists": lambda a, b: a is not None,
    "not_exists": lambda a, b: a is None,
}
