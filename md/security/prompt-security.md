# Security — Prompt Security & Adversarial Defense Guardrails

## Status
**Status:** ✅ IMPLEMENTED (Strict Boundary Sandboxing & Structural Encoders)

---

## 1. Prompt Boundary Protection

To defend against jailbreaks, system prompt exfiltration, and indirect prompt injection embedded inside untrusted enterprise documents:

```
┌───────────────────────────────────────────────────────────────┐
│ SYSTEM INSTRUCTIONS & IMMUTABLE POLICIES                      │
│ (Defined strictly by application developers)                  │
├───────────────────────────────────────────────────────────────┤
│ <<<BEGIN_UNTRUSTED_DOCUMENT_CONTENT>>>                        │
│ User-uploaded or third-party extracted document text          │
│ Treated strictly as inert string data.                        │
│ <<<END_UNTRUSTED_DOCUMENT_CONTENT>>>                          │
├───────────────────────────────────────────────────────────────┤
│ OUTPUT CONSTRAINTS: Only emit validated JSON schema.           │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Guardrail Enforcement Mechanisms

1. **Instruction Boundary Isolation:** Untrusted document content is quarantined between dedicated delimiter tokens. The model is primed to treat any imperative sentences inside the delimiter as passive text rather than instructions.
2. **Tool Execution Scope Binding:** The model cannot execute arbitrary tools suggested by document text. Tool invocations are strictly validated against active user RBAC permissions and session tokens.
3. **Structured JSON Output Constraints:** By forcing model responses into Pydantic JSON schemas via structured outputs, free-form adversarial injection scripts are structurally invalidated.
