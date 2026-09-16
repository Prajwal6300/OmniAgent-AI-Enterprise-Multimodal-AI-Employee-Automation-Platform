"""
OmniAgent AI — Database Agent Schemas
Defines request, response, query plan, and intent data contracts for the Database Agent.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataIntent(str, Enum):
    COUNT = "COUNT"
    LIST = "LIST"
    FILTER = "FILTER"
    AGGREGATION = "AGGREGATION"
    GROUP_BY = "GROUP_BY"
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    MIN_MAX = "MIN_MAX"
    TREND = "TREND"
    COMPARISON = "COMPARISON"
    RANKING = "RANKING"
    SEARCH = "SEARCH"
    UNKNOWN = "UNKNOWN"


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation: str = Field(..., description="High-level operation type: count, aggregation, filter, ranking, etc.")
    tables: list[str] = Field(default_factory=list, description="Target approved database tables")
    filters: list[str] = Field(default_factory=list, description="Filter conditions to apply")
    group_by: list[str] = Field(default_factory=list, description="Columns to group by")
    aggregations: list[str] = Field(default_factory=list, description="Aggregation expressions, e.g. COUNT(*), AVG(time)")
    sort: str | None = Field(default=None, description="Sorting specification e.g. failure_count DESC")
    limit: int = Field(default=100, ge=1, le=1000, description="Safe row limit")


class GeneratedQuery(BaseModel):
    """Structured query object generated for execution. Preserves backward compatibility."""
    model_config = ConfigDict(extra="ignore")

    sql: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_safe: bool = True
    explanation: str = ""


class TableColumnMetadata(BaseModel):
    name: str
    data_type: str
    description: str = ""
    is_primary_key: bool = False
    is_tenant_key: bool = False
    is_foreign_key: bool = False


class ApprovedTableSchema(BaseModel):
    table_name: str
    description: str
    columns: dict[str, str] = Field(default_factory=dict, description="Column name to type map")
    column_details: list[TableColumnMetadata] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)


class DatabaseQueryRequest(BaseModel):
    """
    User query request.
    Tenant ID, organization ID, and role permissions are strictly injected by backend authentication.
    """
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=2000, description="Natural language question about authorized business data")
    limit: int | None = Field(default=None, ge=1, le=500, description="Optional upper bound on rows returned")


class DatabaseResponse(BaseModel):
    """Standardized response contract returned to clients."""
    model_config = ConfigDict(from_attributes=True)

    question: str
    summary: str

    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)

    row_count: int = 0

    query_executed: bool = False
    confidence: float = 0.0

    limited: bool = False
    error: str | None = None
