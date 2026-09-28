# OmniAgent AI — Orchestration Layer

The central cognitive orchestrator connects OmniAgent AI's specialized multimodal agents into a secure, unified AI employee system.

## Architecture

```text
                    USER
                     |
                     v
              Unified AI Chat
                     |
                     v
             Authentication (JWT / RBAC)
                     |
                     v
              Supervisor Agent
                     |
          +----------+----------+
          |          |          |
          v          v          v
      Document     RAG       Database
       Agent       Agent       Agent
          |          |          |
          +----------+----------+
                     |
                     v
                Vision Agent
                     |
                     v
              Reasoning Agent
                     |
              Decision / Analysis
                     |
                     v
                Action Agent
                     |
             +-------+-------+
             |               |
        Approval         No Approval
             |               |
             v               v
        Human Review     Execute Action
             |               |
             +-------+-------+
                     |
                     v
                 Verify
                     |
                     v
                 Audit
                     |
                     v
             Final Response
```

## Supported Flow Modes

1. **Simple Requests**: Single specialist execution via Supervisor routing (e.g. Document parsing, Knowledge search, Database query).
2. **Complex Multi-Agent Requests**: Supervisor routes to multiple agents (e.g., Vision + Database), normalizes evidence, resolves conflicts in Reasoning Agent, and requests Action with Human-In-The-Loop approval.

## Security & Governance
- **Zero-Trust Input**: All OCR, document chunks, DB rows, and prompts inspected for injection patterns.
- **Tenant Isolation**: Mandatory authenticated `organization_id` injected on every call.
- **Safe Transitions**: Prohibits self-recursion and arbitrary jumps.
- **Cryptographic Approval Binding**: SHA-256 HMAC payload binding prevents parameter tampering.
