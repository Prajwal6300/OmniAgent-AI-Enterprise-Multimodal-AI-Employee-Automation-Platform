# Frontend — Web Application Architecture (Next.js 14 App Router)

## Status
**Status:** ✅ IMPLEMENTED (Next.js 14 App Router, React 18, TypeScript, Tailwind CSS & Shadcn UI)

---

## 1. Frontend Architecture Overview

The OmniAgent AI web portal is built with **Next.js 14+ (App Router)**, **React 18**, and **TypeScript (Strict Mode)**. It delivers an enterprise-grade, real-time user interface featuring streaming multi-agent thought streams, interactive PDF/image viewer sidecars, and an approval inbox.

```mermaid
flowchart TD
    A[Browser Client: Next.js 14 App Router] --> B[Root Layout: Theme, Auth, Query Providers]
    
    B --> C[App Routes Hierarchy]
    C --> D[/(auth): Login, Register, Reset]
    C --> E[/(dashboard): AI Employee, Approvals, Workflows, Documents, Audit]
    
    E --> F[Client Components: Shadcn UI + Radix Primitives]
    
    F --> G[Zustand Stores: Active Session, UI State, SSE Stream State]
    F --> H[TanStack React Query v5: REST API Cache & Optimistic Updates]
    
    G --> I[EventSource SSE Connection: /api/v1/chat/sessions/{id}/stream]
    H --> J[Axios HTTP Client: /api/v1/*]
```

---

## 2. Directory Layout (`frontend/src/`)

```text
frontend/src/
├── app/                      # Next.js App Router Pages & Layouts
│   ├── (auth)/               # Unauthenticated Auth Routes (login, register)
│   ├── (dashboard)/          # Authenticated Enterprise Portal Routes
│   │   ├── chat/             # Multimodal AI Employee Chat & Tool Inspector
│   │   ├── approvals/        # Human-in-the-Loop Approval Queue
│   │   ├── workflows/        # Visual Workflow DAG Builder & Execution History
│   │   ├── documents/        # Knowledge Base Ingestion & Vector Explorer
│   │   ├── audit/            # Immutable Audit Ledger Table & Export
│   │   └── settings/         # Organization, Roles & LLM Provider API Keys
│   ├── layout.tsx            # Global Root Layout
│   └── page.tsx              # Landing / Redirect Page
├── components/               # Reusable UI Component Library
│   ├── ui/                   # Shadcn UI Primitives (Button, Dialog, Card, Table)
│   ├── chat/                 # ChatBubble, StreamRenderer, CitationCard, ToolDrawer
│   ├── approvals/            # ApprovalCard, DiffViewer, DecisionModal
│   ├── viewer/               # BoundingBoxImageViewer, PDFHighlightViewer
│   └── layout/               # Sidebar, Header, Breadcrumbs, TenantSwitcher
├── hooks/                    # Custom React Hooks (useChatStream, useAuth, useWebSocket)
├── stores/                   # Zustand Global Stores (authStore, uiStore, chatStore)
├── services/                 # Axios Typed API Services (chatService, docService, etc.)
└── types/                    # TypeScript Data Interfaces & Enums
```
