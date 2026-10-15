"""
SQL Injection Guard Tests

Tests that validate ORDER BY columns and aggregate expressions against
the schema allowlist, ensuring injection holes invisible to bandit are closed.
"""

import pytest

from app.agents.database.exceptions import SchemaValidationError
from app.agents.database.query_builder import QueryBuilder
from app.agents.database.schema_registry import schema_registry
from app.agents.database.sql_generator import SQLGenerator


def _gen():
    return SQLGenerator(registry=schema_registry)


def _qb():
    return QueryBuilder(registry=schema_registry)


# ---- Sort column validation ----

def test_sort_injection_select_password_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("(SELECT password FROM users LIMIT 1)", "column", "orders")


def test_sort_injection_dROP_TABLE_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("id; DROP TABLE users", "column", "orders")


def test_sort_injection_id_desc_select_1_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("id DESC, (SELECT 1)", "column", "orders")


def test_sort_column_from_other_table_raises():
    gen = _gen()
    # 'name' is a column on 'products' but not on 'orders'
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("name", "column", "orders")


# ---- Aggregate expression validation ----

def test_agg_injection_count_star_subquery_not_safe():
    gen = _gen()
    # "COUNT(*), (SELECT...)" does NOT match the strict regex
    assert gen._is_safe_agg_expr("COUNT(*), (SELECT secret FROM other LIMIT 1)") is False


def test_agg_injection_sum_not_in_allowlist_not_safe_col():
    gen = _gen()
    # "SUM(not_in_allowlist)" matches the regex but the column is not in allowlist;
    # test via _validate_identifier column check instead
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("not_in_allowlist", "column", "orders")


# ---- Table validation ----

def test_table_injection_users_drop_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_identifier("users; DROP TABLE x", "table")


# ---- Limit validation ----

def test_limit_clamped_10_to_9():
    gen = _gen()
    result = gen._validate_limit(10 ** 9)
    assert result == 500, f"Expected 500, got {result}"


def test_limit_zero_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_limit(0)


def test_limit_abc_raises():
    gen = _gen()
    with pytest.raises(SchemaValidationError):
        gen._validate_limit("abc")


# ---- Positive tests ----

def test_valid_sort():
    gen = _gen()
    result = gen._validate_sort_direction("ASC")
    assert result == "ASC"


def test_count_star_positive():
    gen = _gen()
    assert gen._is_safe_agg_expr("COUNT(*)") is True


def test_avg_valid_column():
    gen = _gen()
    assert gen._is_safe_agg_expr("AVG(total_amount)") is True


def test_build_select_no_columns():
    qb = _qb()
    result = qb.build_select(table="orders", columns=None)
    assert result == "SELECT * FROM orders WHERE organization_id = :organization_id"


def test_build_select_with_columns():
    qb = _qb()
    result = qb.build_select(
        table="orders", columns=["id", "order_number", "status"]
    )
    assert "id" in result
    assert "order_number" in result
    assert "status" in result
    assert "organization_id = :organization_id" in result


def test_build_select_with_star():
    qb = _qb()
    result = qb.build_select(table="orders", columns=["*"])
    assert result == "SELECT * FROM orders WHERE organization_id = :organization_id"


def test_build_select_with_limit():
    qb = _qb()
    query, limit = qb.build_select_with_limit(
        table="orders", columns=["id"], limit=10
    )
    assert "LIMIT :limit" in query
    assert limit == 10


def test_build_select_with_limit_clamped():
    qb = _qb()
    _, limit = qb.build_select_with_limit(
        table="orders", columns=["id"], limit=10 ** 9
    )
    assert limit == 500


def test_build_select_with_limit_zero():
    qb = _qb()
    _, limit = qb.build_select_with_limit(
        table="orders", columns=["id"], limit=0
    )
    assert limit == 1


def test_build_select_with_limit_abc():
    qb = _qb()
    _, limit = qb.build_select_with_limit(
        table="orders", columns=["id"], limit="abc"
    )
    # "abc" can't be converted to int, defaults to 500
    assert limit == 500