"""
OmniAgent AI — Automation Step Executor
Executes individual workflow steps: agent dispatch, condition checks, approvals, and enterprise actions.
"""

import time
from typing import Any

from app.automation.conditions.evaluator import ConditionEvaluator
from app.automation.conditions.rules import Rule
from app.automation.engine.state import StepRunResult, WorkflowRunState


class StepExecutor:
    """Executes single workflow steps securely within organization context."""

    def __init__(self, session: Any = None):
        self.session = session
        self.evaluator = ConditionEvaluator()

    async def execute_step(
        self,
        step: dict[str, Any],
        step_index: int,
        run_state: WorkflowRunState,
    ) -> StepRunResult:
        stype = step.get("type", "").lower()
        t0 = time.time()
        org_id = run_state.organization_id

        try:
            if stype == "agent":
                agent_name = step.get("agent", "")
                from app.orchestration.executor import OrchestrationAgentExecutor
                orch_exec = OrchestrationAgentExecutor()

                # Build simulated state for agent execution
                prompt = step.get("prompt") or run_state.context.get("message") or "Analyze step data"
                exec_state = {
                    "organization_id": org_id,
                    "user_id": run_state.context.get("user_id", "workflow_user"),
                    "request_id": f"wf_{run_state.run_id}_{step_index}",
                    "user_message": prompt,
                    "context": run_state.context,
                    "session": self.session,
                }
                res = await orch_exec.execute_agent(agent_name, exec_state)
                output = res.get("output", {})
                # Store in context under agent name
                run_state.context[agent_name] = output

                elapsed_ms = round((time.time() - t0) * 1000, 2)
                return StepRunResult(
                    step_index=step_index,
                    step_type="agent",
                    name=agent_name,
                    status="COMPLETED",
                    output=output,
                    duration_ms=elapsed_ms,
                )

            elif stype == "condition":
                rule = Rule(
                    field=step.get("field", ""),
                    operator=step.get("operator", "=="),
                    expected_value=step.get("value") or step.get("expected_value"),
                )
                passed = self.evaluator.evaluate(rule, run_state.context)
                run_state.context[f"step_{step_index}_condition"] = passed
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                return StepRunResult(
                    step_index=step_index,
                    step_type="condition",
                    name=f"Condition: {rule.field} {rule.operator} {rule.expected_value}",
                    status="COMPLETED" if passed else "SKIPPED",
                    output={"passed": passed},
                    duration_ms=elapsed_ms,
                )

            elif stype == "approval":
                is_req = step.get("required", True)
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                if is_req and not run_state.context.get("approval_granted"):
                    return StepRunResult(
                        step_index=step_index,
                        step_type="approval",
                        name="Human Approval Gate",
                        status="PAUSED",
                        output={"approval_required": True},
                        duration_ms=elapsed_ms,
                    )
                return StepRunResult(
                    step_index=step_index,
                    step_type="approval",
                    name="Human Approval Gate",
                    status="COMPLETED",
                    output={"approved": True},
                    duration_ms=elapsed_ms,
                )

            elif stype == "action":
                act_name = step.get("action", "").lower()
                from app.agents.action.agent import ActionAgent
                from app.agents.action.schemas import ActionContext, ActionRequest
                agent = ActionAgent(session=self.session)
                act_ctx = ActionContext(
                    user_id=str(run_state.context.get("user_id", "workflow_user")),
                    organization_id=org_id,
                )
                input_data = dict(step.get("input") or run_state.context.get(f"{act_name}_input") or {})
                if act_name == "send_notification":
                    input_data.setdefault("user_id", act_ctx.user_id)
                    input_data.setdefault("message", input_data.get("title", "Workflow Notification"))
                elif act_name == "create_ticket":
                    input_data.setdefault("description", input_data.get("title", "Workflow Ticket"))
                act_req = ActionRequest(
                    action_type=act_name,
                    input=input_data,
                    approval_id=run_state.context.get("approval_id"),
                )
                res = await agent.execute(act_req, act_ctx, session=self.session)
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                output = res.model_dump() if hasattr(res, "model_dump") else dict(res)
                return StepRunResult(
                    step_index=step_index,
                    step_type="action",
                    name=act_name,
                    status="COMPLETED" if res.verified or res.success else "FAILED",
                    output=output,
                    duration_ms=elapsed_ms,
                )

            else:
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                return StepRunResult(
                    step_index=step_index,
                    step_type=stype,
                    status="COMPLETED",
                    output={},
                    duration_ms=elapsed_ms,
                )

        except Exception as exc:  # noqa: BLE001
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            return StepRunResult(
                step_index=step_index,
                step_type=stype,
                status="FAILED",
                error=str(exc),
                duration_ms=elapsed_ms,
            )
