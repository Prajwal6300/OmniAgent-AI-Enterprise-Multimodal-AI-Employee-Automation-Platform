from typing import ClassVar


class ToolPermissionGuard:
    # Role-based permission map for tools
    TOOL_PERMISSIONS: ClassVar[dict[str, list[str]]] = {
        "db_read": ["Admin", "Supervisor", "Operator"],
        "email_send": ["Admin", "Supervisor", "Operator"],
        "ticket_create": ["Admin", "Supervisor", "Operator"],
        "storage_delete": ["Admin"],
    }

    @classmethod
    def check_permission(cls, tool_name: str, user_role: str) -> bool:
        allowed = cls.TOOL_PERMISSIONS.get(tool_name, ["Admin"])
        return user_role in allowed

