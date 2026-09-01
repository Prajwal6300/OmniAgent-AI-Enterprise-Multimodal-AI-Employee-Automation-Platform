# Integrations — Generic External API & OAuth2 Framework

## Status
**Status:** ✅ IMPLEMENTED (Generic HTTP Tool Builder & OAuth2 Client)

---

## 1. Generic External API Framework

OmniAgent AI provides a generic declarative connector builder allowing system administrators to integrate third-party REST and GraphQL APIs into the agent tool catalog without writing custom Python code.

```json
{
  "integration_id": "int_zendesk_support",
  "name": "Zendesk Support API",
  "base_url": "https://enterprise.zendesk.com/api/v2",
  "auth_type": "bearer_token",
  "secret_key_ref": "vault://integrations/zendesk/api_token",
  "endpoints": [
    {
      "name": "create_ticket",
      "method": "POST",
      "path": "/tickets.json",
      "risk_level": "LOW",
      "required_params": ["subject", "comment_body", "priority"],
      "headers": { "Accept": "application/json" }
    }
  ]
}
```

---

## 2. Dynamic Tool Synthesis

The backend dynamically registers these endpoints into LangGraph tool registries, allowing agents to discover and invoke external enterprise tools with strict schema adherence.
