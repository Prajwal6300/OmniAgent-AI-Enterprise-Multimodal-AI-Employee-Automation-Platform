from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_run import AgentRun, ToolCall

class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(self, run: AgentRun) -> AgentRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: UUID) -> Optional[AgentRun]:
        stmt = select(AgentRun).where(AgentRun.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_tool_call(self, tool_call: ToolCall) -> ToolCall:
        self.session.add(tool_call)
        await self.session.flush()
        return tool_call
