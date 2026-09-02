from tools.common.permissions import ToolPermissionGuard

def test_tool_permission_guard():
    assert ToolPermissionGuard.check_permission("storage_delete", "Admin") is True
    assert ToolPermissionGuard.check_permission("storage_delete", "Viewer") is False
