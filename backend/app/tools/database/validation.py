def validate_sql(sql: str) -> bool:
    sql_upper = sql.upper()
    return not any(word in sql_upper for word in ["DROP", "DELETE", "TRUNCATE", "UPDATE"])
