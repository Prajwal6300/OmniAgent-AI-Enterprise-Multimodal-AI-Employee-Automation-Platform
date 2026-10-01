# OmniAgent AI — Automation Engine

Enterprise workflow execution engine coordinating multi-agent steps, deterministic condition rules, human-in-the-loop approvals, and external actions.

## Features
- **Triggers**: MANUAL, EVENT, SCHEDULE.
- **Step Types**:
  - `agent`: Dispatches to specialized agents (`vision_agent`, `database_agent`, `reasoning_agent`, `rag_agent`, `document_agent`, `action_agent`).
  - `condition`: Safe deterministic evaluation (equals, contains, greater_than, etc.) without dynamic `eval()`.
  - `approval`: Pauses execution for human authorization when required.
  - `action`: Dispatches authorized enterprise operations via Action Agent.
- **Safety Limits**: Max 30 steps, 300 second execution ceiling, tenant isolation.
