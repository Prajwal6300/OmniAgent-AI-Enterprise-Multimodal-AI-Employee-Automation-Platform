from typing import Dict, Any, Callable
from tools.common.permissions import ToolPermissionGuard
from tools.common.schemas import ToolExecutionRequest, ToolExecutionResult

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    async def execute(self, req: ToolExecutionRequest, user_role: str) -> ToolExecutionResult:
        if not ToolPermissionGuard.check_permission(req.tool_name, user_role):
            return ToolExecutionResult(success=False, error=f"Permission denied for tool: {req.tool_name}")

        tool_fn = self._tools.get(req.tool_name)
        if not tool_fn:
            return ToolExecutionResult(success=False, error=f"Tool not found: {req.tool_name}")

        try:
            res = await tool_fn(req.parameters)
            return ToolExecutionResult(success=True, data=res)
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))

registry = ToolRegistry()
