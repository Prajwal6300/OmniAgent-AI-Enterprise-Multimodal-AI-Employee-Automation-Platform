# Integrations — Enterprise System Connectors Overview

## Status
**Status:** ✅ IMPLEMENTED (Connector Framework & Credentials Vault)

---

## 1. Connector Abstraction Architecture

OmniAgent AI communicates with enterprise systems through an extensible **Connector Abstraction Layer** (`app.integrations.connectors`). Connectors handle rate limiting, token refresh, retry logic with exponential backoff, and strict payload serialization.

```mermaid
flowchart TD
    A[Action Agent Tool Invocation] --> B[Connector Factory Manager]
    
    B --> C{Select Target Connector}
    
    C -->|Email| D[SMTP / IMAP / SendGrid Connector]
    C -->|ChatOps| E[Slack & Microsoft Teams Connector]
    C -->|ERP & DB| F[SAP S/4HANA & Oracle REST Connector]
    C -->|Ticketing| G[Atlassian Jira & ServiceNow Connector]
    C -->|Web Intelligence| H[Tavily & DuckDuckGo Search Connector]
    
    D & E & F & G & H --> I[Encrypted Secrets Vault - Vault/KMS]
    I --> J[Execute External HTTPS Request with Idempotency Key]
```

---

## 2. Secrets & Credential Management

All third-party API keys, OAuth2 client secrets, and SMTP credentials are encrypted at rest using AES-256-GCM in the tenant integration settings table and decrypted in-memory only during tool execution.
