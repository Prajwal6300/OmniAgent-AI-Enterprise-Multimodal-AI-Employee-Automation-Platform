# Architecture Decision Records — ADR 001: Multi-Agent Orchestration & State Graphs

## Status
**Status:** ✅ ACCEPTED & IMPLEMENTED

---

## 1. Context & Problem Statement
Enterprise automation involves multi-step reasoning, cross-modal ingestion, deterministic policy verification, and human approvals. Single monolithic LLM prompts fail on long-horizon tasks due to context pollution, attention degradation, and an inability to compartmentalize permissions.

## 2. Decision: LangGraph Supervisor Architecture
We decided to adopt **LangGraph** to model multi-agent workflows as a stateful Directed Acyclic Graph (DAG) coordinated by a central **Supervisor Agent**.

### Alternatives Considered
* **Monolithic Single-Prompt LLM:** Rejected due to context limits, hallucination rates on complex multi-step instructions, and lack of modular security boundaries.
* **Decentralized Multi-Agent Swarm (AutoGPT / CrewAI):** Rejected due to non-deterministic looping, high token waste, and lack of strict state transition controls.

### Consequences & Trade-Offs
* **Benefits:** Modular agent roles, deterministic sub-task delegation, clear audit trails, and seamless state checkpointing in Redis and PostgreSQL.
* **Trade-Offs:** Slightly higher architectural complexity and orchestration latency (~300ms overhead for supervisor planning).
