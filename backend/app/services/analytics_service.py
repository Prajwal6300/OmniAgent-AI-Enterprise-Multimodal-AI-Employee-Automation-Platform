"""
OmniAgent AI — Analytics Service
Performs real tenant-isolated aggregations across agent runs, token consumption,
cost metrics, p50/p95/p99 latencies, and human approval queues.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import numpy as np
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentRun
from app.models.approval import Approval
from app.models.workflow import WorkflowRun

logger = structlog.get_logger(__name__)


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Computes real operational analytics strictly scoped to the authenticated organization.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # 1. Agent run aggregations
        runs_stmt = (
            select(AgentRun)
            .where(
                AgentRun.organization_id == organization_id,
                AgentRun.started_at >= cutoff,
            )
        )
        runs_res = await self.session.execute(runs_stmt)
        runs = list(runs_res.scalars().all())

        total_runs = len(runs)
        total_tokens = sum(r.total_tokens for r in runs)
        total_cost_usd = float(sum(r.cost_usd for r in runs))

        successful_runs = sum(1 for r in runs if r.status in ("COMPLETED", "SUCCESS"))
        success_rate = round((successful_runs / total_runs * 100), 2) if total_runs > 0 else 100.0

        # Latency calculations
        latencies = [r.latency_ms for r in runs if r.latency_ms is not None and r.latency_ms > 0]
        if latencies:
            latencies_sorted = sorted(latencies)
            p50 = int(np.percentile(latencies_sorted, 50))
            p95 = int(np.percentile(latencies_sorted, 95))
            p99 = int(np.percentile(latencies_sorted, 99))
            avg_latency = int(sum(latencies) / len(latencies))
        else:
            p50 = p95 = p99 = avg_latency = 0

        # Agent breakdown
        breakdown_stmt = (
            select(
                AgentRun.agent_name,
                func.count(AgentRun.id).label("count"),
                func.sum(AgentRun.total_tokens).label("tokens"),
                func.sum(AgentRun.cost_usd).label("cost"),
            )
            .where(
                AgentRun.organization_id == organization_id,
                AgentRun.started_at >= cutoff,
            )
            .group_by(AgentRun.agent_name)
        )
        breakdown_res = await self.session.execute(breakdown_stmt)
        agent_breakdown = [
            {
                "agent": row.agent_name,
                "count": row.count,
                "tokens": row.tokens or 0,
                "cost_usd": float(row.cost or 0.0),
            }
            for row in breakdown_res.all()
        ]

        # 2. Pending approvals count
        appr_stmt = (
            select(func.count(Approval.id))
            .where(
                Approval.organization_id == organization_id,
                Approval.status.in_(["PENDING", "PENDING_SECOND_APPROVAL"]),
            )
        )
        appr_res = await self.session.execute(appr_stmt)
        pending_approvals = appr_res.scalar() or 0

        # 3. Workflow runs count
        wf_stmt = (
            select(func.count(WorkflowRun.id))
            .where(
                WorkflowRun.organization_id == organization_id,
                WorkflowRun.started_at >= cutoff,
            )
        )
        wf_res = await self.session.execute(wf_stmt)
        total_workflow_runs = wf_res.scalar() or 0

        return {
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate_percent": success_rate,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 4),
            "pending_approvals": pending_approvals,
            "total_workflow_runs": total_workflow_runs,
            "latency": {
                "avg_ms": avg_latency,
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "agent_breakdown": agent_breakdown,
        }
