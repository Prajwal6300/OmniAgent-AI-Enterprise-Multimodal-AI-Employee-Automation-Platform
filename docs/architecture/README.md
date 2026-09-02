# OmniAgent AI — System Architecture Documentation

This directory contains technical engineering architecture documentation for OmniAgent AI.
For the exhaustive 139-document specification suite, refer to the [`md/`](../../md/README.md) directory.

## Core Architectural Pillars
1. **Modular Monolith Design**: Clear boundaries between API, Services, Agents, Multimodal Engine, and Tools.
2. **Hierarchical Supervisor Pattern**: Master supervisor agent decomposes high-level intent and orchestrates specialized worker agents.
3. **Deterministic Governance & Safety**: Tool execution is gatekept by RBAC, schema validation, and human-in-the-loop approvals.
4. **Unified Multimodal Ingestion**: Normalizes heterogeneous media into structured context for grounded reasoning.
