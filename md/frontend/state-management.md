# Frontend — State Management Strategy (Zustand & React Query)

## Status
**Status:** ✅ IMPLEMENTED (Zustand Client Stores + TanStack Query Server State)

---

## 1. Dual-Tier State Architecture

OmniAgent AI separates ephemeral client-side UI state from server data caching:

```mermaid
flowchart TD
    subgraph Client_State [Zustand Ephemeral State Stores]
        AuthStore[useAuthStore: Tokens, User Profile, Tenant ID]
        UIStore[useUIStore: Sidebar Toggle, Active Sidecar Tab, Theme]
        ChatStore[useChatStore: Active Session ID, Streaming Buffers]
    end

    subgraph Server_State [TanStack React Query v5 Cache]
        DocCache[useDocumentsQuery: Ingested Knowledge Base]
        ApprCache[useApprovalsQuery: Pending Human Approvals Queue]
        WFCache[useWorkflowsQuery: Configured DAGs & Run History]
        AuditCache[useAuditLogsQuery: Filtered Audit Trail]
    end

    Browser_Events[User & WebSocket Events] --> Client_State
    REST_API[FastAPI Backend] --> Server_State
```

---

## 2. Streaming State Handler (`useChatStream`)

```typescript
export const useChatStream = (sessionId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeStep, setActiveStep] = useState<AgentStep | null>(null);

  const streamPrompt = (prompt: string, s3Keys: string[]) => {
    const eventSource = new EventSource(
      `/api/v1/chat/sessions/${sessionId}/stream?prompt=${encodeURIComponent(prompt)}`
    );

    eventSource.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'token') {
        // Append streaming text token
      } else if (payload.type === 'agent_step') {
        setActiveStep(payload.data);
      } else if (payload.type === 'done') {
        eventSource.close();
      }
    };
  };

  return { messages, activeStep, streamPrompt };
};
```
