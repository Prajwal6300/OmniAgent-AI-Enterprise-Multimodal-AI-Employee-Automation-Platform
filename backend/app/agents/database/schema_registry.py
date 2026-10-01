"""
OmniAgent AI — Controlled Schema Registry & Discovery
Provides strict allowlisted schema exposure for business data.
Guarantees the LLM never sees passwords, credentials, system tables, or raw DDL.
"""

from typing import Any

# Approved business tables that can be queried by the Database Agent
ALLOWED_TABLES: set[str] = {
    "orders",
    "products",
    "vendors",
    "machines",
    "production_records",
    "maintenance_requests",
    "documents",
    "agent_runs",
    "approvals",
    "workflows",
    "workflow_runs",
    "notifications",
    "departments",
}

# Strict column allowlist for each table to prevent exposing internal or sensitive fields
COLUMN_ALLOWLIST: dict[str, set[str]] = {
    "orders": {
        "id", "organization_id", "order_number", "customer_name", "status", "total_amount", "created_at", "updated_at"
    },
    "products": {
        "id", "organization_id", "name", "sku", "category", "price", "usage_count", "is_active", "created_at"
    },
    "vendors": {
        "id", "organization_id", "name", "contact_email", "total_purchases", "rating", "created_at"
    },
    "machines": {
        "id", "organization_id", "name", "machine_code", "department_id", "status", "failure_count", "created_at", "updated_at"
    },
    "production_records": {
        "id", "organization_id", "machine_id", "batch_number", "status", "defect_count", "production_time_hours", "notes", "created_at"
    },
    "maintenance_requests": {
        "id", "organization_id", "machine_id", "title", "status", "priority", "created_at"
    },
    "documents": {
        "id", "organization_id", "uploaded_by", "file_name", "file_type", "file_size_bytes", "processing_status", "created_at"
    },
    "agent_runs": {
        "id", "organization_id", "conversation_id", "user_id", "agent_name", "task_description", "status", "started_at", "completed_at", "latency_ms", "total_tokens", "cost_usd"
    },
    "approvals": {
        "id", "organization_id", "action_type", "risk_level", "reason", "status", "created_at"
    },
    "workflows": {
        "id", "organization_id", "name", "description", "trigger_type", "is_active", "created_at"
    },
    "workflow_runs": {
        "id", "organization_id", "workflow_id", "status", "started_at", "finished_at"
    },
    "notifications": {
        "id", "organization_id", "user_id", "title", "message", "notification_type", "is_read", "created_at"
    },
    "departments": {
        "id", "organization_id", "name", "code", "created_at"
    }
}

# Human-readable table descriptions for LLM prompt grounding
TABLE_DESCRIPTIONS: dict[str, str] = {
    "orders": "Customer sales orders, fulfillment status (PENDING, PROCESSING, COMPLETED, CANCELLED), and monetary totals",
    "products": "Catalog of industrial and enterprise products, SKUs, pricing, categories, and cumulative usage counts",
    "vendors": "Suppliers and vendors, total purchase volume, performance ratings, and contact info",
    "machines": "Manufacturing plant machines, equipment codes, operational status (OPERATIONAL, MAINTENANCE, FAILED), and total failure counts",
    "production_records": "Factory production inspection records, batches, quality inspection status (PASSED, FAILED), defect counts, and production run times in hours",
    "maintenance_requests": "Equipment maintenance tickets, severity/priority levels, and resolution status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
    "documents": "Uploaded enterprise files, documents, processing statuses, file sizes, and creation timestamps",
    "agent_runs": "Execution traces of AI employees and specialized agents, task descriptions, tokens, cost, and latency",
    "approvals": "Governance and human-in-the-loop approval requests, actions, risk levels, and status",
    "workflows": "Configured enterprise automation workflows, triggers, and active status",
    "workflow_runs": "Execution instances of automation workflows and completion statuses",
    "notifications": "Enterprise alerts and notifications sent to operators and supervisors",
    "departments": "Organizational departments, departmental business codes, and operational units"
}

# Column data types for schema grounding
COLUMN_TYPES: dict[str, dict[str, str]] = {
    "orders": {
        "id": "uuid", "organization_id": "uuid", "order_number": "string", "customer_name": "string",
        "status": "string", "total_amount": "numeric", "created_at": "datetime", "updated_at": "datetime"
    },
    "products": {
        "id": "uuid", "organization_id": "uuid", "name": "string", "sku": "string", "category": "string",
        "price": "numeric", "usage_count": "integer", "is_active": "boolean", "created_at": "datetime"
    },
    "vendors": {
        "id": "uuid", "organization_id": "uuid", "name": "string", "contact_email": "string",
        "total_purchases": "numeric", "rating": "numeric", "created_at": "datetime"
    },
    "machines": {
        "id": "uuid", "organization_id": "uuid", "name": "string", "machine_code": "string",
        "department_id": "uuid", "status": "string", "failure_count": "integer", "created_at": "datetime", "updated_at": "datetime"
    },
    "production_records": {
        "id": "uuid", "organization_id": "uuid", "machine_id": "uuid", "batch_number": "string",
        "status": "string", "defect_count": "integer", "production_time_hours": "numeric", "notes": "text", "created_at": "datetime"
    },
    "maintenance_requests": {
        "id": "uuid", "organization_id": "uuid", "machine_id": "uuid", "title": "string",
        "status": "string", "priority": "string", "created_at": "datetime"
    },
    "documents": {
        "id": "uuid", "organization_id": "uuid", "uploaded_by": "uuid", "file_name": "string",
        "file_type": "string", "file_size_bytes": "bigint", "processing_status": "string", "created_at": "datetime"
    },
    "agent_runs": {
        "id": "uuid", "organization_id": "uuid", "conversation_id": "uuid", "user_id": "uuid",
        "agent_name": "string", "task_description": "text", "status": "string", "started_at": "datetime",
        "completed_at": "datetime", "latency_ms": "integer", "total_tokens": "integer", "cost_usd": "numeric"
    },
    "approvals": {
        "id": "uuid", "organization_id": "uuid", "action_type": "string", "risk_level": "string",
        "reason": "text", "status": "string", "created_at": "datetime"
    },
    "workflows": {
        "id": "uuid", "organization_id": "uuid", "name": "string", "description": "text",
        "trigger_type": "string", "is_active": "boolean", "created_at": "datetime"
    },
    "workflow_runs": {
        "id": "uuid", "organization_id": "uuid", "workflow_id": "uuid", "status": "string",
        "started_at": "datetime", "finished_at": "datetime"
    },
    "notifications": {
        "id": "uuid", "organization_id": "uuid", "user_id": "uuid", "title": "string",
        "message": "text", "notification_type": "string", "is_read": "boolean", "created_at": "datetime"
    },
    "departments": {
        "id": "uuid", "organization_id": "uuid", "name": "string", "code": "string", "created_at": "datetime"
    }
}


class SchemaRegistry:
    """
    Controlled registry for authorized database schema metadata.
    Provides verified schema context to the LLM and enforces table/column boundaries.
    """

    def __init__(self):
        self.allowed_tables = set(ALLOWED_TABLES)
        self.column_allowlist = {k: set(v) for k, v in COLUMN_ALLOWLIST.items()}
        self.table_descriptions = dict(TABLE_DESCRIPTIONS)
        self.column_types = {k: dict(v) for k, v in COLUMN_TYPES.items()}

    def is_table_allowed(self, table_name: str) -> bool:
        """Returns True if the table is explicitly in the approved business allowlist."""
        return table_name.lower().strip() in self.allowed_tables

    def is_column_allowed(self, table_name: str, column_name: str) -> bool:
        """Returns True if the column is explicitly in the approved allowlist for the table."""
        tbl = table_name.lower().strip()
        col = column_name.lower().strip()
        if tbl not in self.column_allowlist:
            return False
        return col in self.column_allowlist[tbl]

    def get_approved_schema(self) -> dict[str, Any]:
        """Returns full structured approved schema metadata."""
        schema = {}
        for table in sorted(self.allowed_tables):
            schema[table] = {
                "description": self.table_descriptions.get(table, ""),
                "columns": self.column_types.get(table, {})
            }
        return schema

    def identify_relevant_tables(self, question: str) -> list[str]:
        """
        Heuristically matches relevant business tables from natural language text.
        Returns a list of approved table names.
        """
        q = question.lower()
        matched: set[str] = set()

        # Production records & inspections
        if any(w in q for w in ["inspection", "inspections", "defect", "defects", "production failure", "batch", "production time"]):
            matched.add("production_records")
        if "production" in q and not any(w in q for w in ["product", "products"]):
            matched.add("production_records")

        # Machines & equipment
        if any(w in q for w in ["machine", "machines", "equipment", "cnc", "welder", "stamper"]):
            matched.add("machines")
            if any(w in q for w in ["failure", "failures", "fail", "failed"]):
                matched.add("machines")
                matched.add("production_records")

        # Orders
        if any(w in q for w in ["order", "orders", "pending order", "sales order"]):
            matched.add("orders")

        # Products
        if any(w in q for w in ["product", "products", "sku", "skus", "usage", "top 10 products", "top products"]):
            matched.add("products")

        # Vendors
        if any(w in q for w in ["vendor", "vendors", "supplier", "suppliers", "purchase amount by vendor", "vendor agreement"]):
            matched.add("vendors")

        # Maintenance
        if any(w in q for w in ["maintenance", "maintenance request", "maintenance ticket", "repair"]):
            matched.add("maintenance_requests")

        # Documents
        if any(w in q for w in ["document", "documents", "file", "uploaded files", "files"]):
            matched.add("documents")

        # Agent runs & traces
        if any(w in q for w in ["agent run", "agent runs", "failed agent", "agent latency", "token count", "cost"]):
            matched.add("agent_runs")

        # Approvals
        if any(w in q for w in ["approval", "approvals", "pending approval"]):
            matched.add("approvals")

        # Workflows
        if any(w in q for w in ["workflow", "workflows", "workflow run"]):
            matched.add("workflows")
            matched.add("workflow_runs")

        # Notifications
        if any(w in q for w in ["notification", "notifications", "alert", "alerts"]):
            matched.add("notifications")

        # Departments
        if any(w in q for w in ["department", "departments"]):
            matched.add("departments")

        return sorted(matched)

    def format_schema_for_prompt(self, relevant_tables: list[str] | None = None) -> str:
        """
        Formats approved schema into concise, sanitized markdown context for LLM prompts.
        Only presents approved business tables and approved columns.
        """
        tables = relevant_tables if relevant_tables else sorted(self.allowed_tables)
        valid_tables = [t for t in tables if t in self.allowed_tables]
        if not valid_tables:
            valid_tables = sorted(self.allowed_tables)


        lines = ["# APPROVED BUSINESS DATABASE SCHEMA (READ-ONLY)"]
        for table in valid_tables:
            desc = self.table_descriptions.get(table, "")
            lines.append(f"\nTable: `{table}`")
            lines.append(f"Description: {desc}")
            lines.append("Columns:")
            cols = self.column_types.get(table, {})
            for col_name, col_type in cols.items():
                lines.append(f"  - `{col_name}` ({col_type})")

        return "\n".join(lines)


# Global registry singleton
schema_registry = SchemaRegistry()
