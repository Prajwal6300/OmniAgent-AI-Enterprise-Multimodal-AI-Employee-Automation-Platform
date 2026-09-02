from tools.common.permissions import ToolPermissionGuard

def test_unregistered_tool_fails_safe():
    assert ToolPermissionGuard.check_permission("unregistered_hazardous_tool", "Operator") is False
