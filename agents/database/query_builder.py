class QueryBuilder:
    def build_select(self, table: str, columns: list, filters: dict) -> str:
        return f"SELECT {', '.join(columns)} FROM {table}"
