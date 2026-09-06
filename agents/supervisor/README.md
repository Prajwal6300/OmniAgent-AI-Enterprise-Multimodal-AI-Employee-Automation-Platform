# OmniAgent AI — Supervisor Agent

The **Supervisor Agent** is the central orchestrator and gateway of OmniAgent AI. It processes incoming enterprise user prompts, determines user intent, classifies required capabilities, maps tasks to future specialist agents, assesses operational risks (human-in-the-loop approvals and tool requirements), and generates structured task plans.

---

## 1. Responsibilities

```
User Request
      ↓
Supervisor Agent
      ↓
Validate Request
      ↓
Classify Intent
      ↓
Determine Required Capability
      ↓
Select Target Agent
      ↓
Determine Risk & Approvals
      ↓
Create Structured Task Plan
      ↓
Validate Decision & Safeguards
      ↓
Return Structured Routing Decision
```

### What the Supervisor Agent Does:
- Evaluates incoming natural language requests and attached contextual metadata.
- Validates input format and blocks empty or oversized payloads.
- Classifies requests into enterprise task types (e.g. `DOCUMENT_ANALYSIS`, `DATABASE_QUERY`, `KNOWLEDGE_SEARCH`, etc.).
- Maps tasks to target agents (`document_agent`, `vision_agent`, `rag_agent`, `database_agent`, `reasoning_agent`, `action_agent`, `supervisor`).
- Evaluates risk levels, detecting destructive actions (deletion, dropping tables) and enforcing `requires_approval=True`.
- Generates a concise operational task plan.
- Guarantees fail-safe responses using structured fallbacks if upstream errors or timeouts occur.

### What the Supervisor Agent Does NOT Do (Today's Non-Goals):
- Does NOT execute worker agents.
- Does NOT execute external tools, send live emails, or modify databases.
- Does NOT expose hidden chain-of-thought or internal reasoning.

---

## 2. Directory Structure

```
agents/supervisor/
├── __init__.py          # Package exports and interface
├── agent.py             # SupervisorAgent class implementation
├── state.py             # Strongly typed SupervisorState TypedDict
├── graph.py             # Compiled LangGraph state machine definition
├── nodes.py             # Isolated atomic LangGraph step nodes
├── router.py            # Capability-to-agent routing matrix and deterministic classifier
├── schemas.py           # Pydantic v2 schemas (SupervisorDecision, etc.)
├── prompts.py           # System instructions, strict boundaries, and templates
├── providers.py         # LLM abstraction with MockLLMProvider and HybridProvider
├── exceptions.py        # Supervisor-specific exception classes
└── README.md            # Developer guide
```

---

## 3. Usage Example

```python
import asyncio
from agents.supervisor import SupervisorAgent

async def main():
    supervisor = SupervisorAgent()
    decision = await supervisor.analyze(
        message="Summarize this financial invoice and check for errors.",
        user_id="user_123",
        organization_id="org_456"
    )

    print("Selected Agent:", decision.selected_agent)
    print("Task Type:", decision.task_type)
    print("Requires Approval:", decision.requires_approval)
    print("Plan:", decision.task_plan)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Testing

Run tests without requiring external paid APIs:

```bash
python -m pytest tests/unit/agents/test_supervisor.py -v
python -m pytest tests/security/agents/test_supervisor_security.py -v
```
