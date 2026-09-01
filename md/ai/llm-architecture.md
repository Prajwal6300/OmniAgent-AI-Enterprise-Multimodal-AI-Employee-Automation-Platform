# AI Subsystems — Multi-Model Gateway & LLM Architecture

## Status
**Status:** ✅ IMPLEMENTED (Dynamic Model Routing & Fallback Gateway)

---

## 1. Overview & Multi-Model Strategy

OmniAgent AI avoids vendor lock-in by implementing an abstraction gateway that dynamically routes requests to the optimal foundation model based on task complexity, modality, context window requirements, data sovereignty policies, and latency budgets.

```mermaid
flowchart TD
    A[Agent Subsystem Request] --> B[Model Gateway Router]
    
    B --> C{Determine Task Classification}
    
    C -->|Complex Reasoning & Synthesis| D[Tier 1: Claude 3.5 Sonnet / GPT-4o]
    C -->|High-Speed / Low-Cost Sub-Tasks| E[Tier 2: Claude 3.5 Haiku / GPT-4o-mini]
    C -->|Long-Context Document Ingestion| F[Tier 3: Gemini 1.5 Pro - 2M Context]
    C -->|Air-Gapped / Privacy-Restricted| G[Tier 4: Local Ollama - Llama 3.3 70B / Qwen 2.5]
    
    D & E & F & G --> H{Provider Available & Healthy?}
    
    H -->|Yes| I[Execute Inference Stream]
    H -->|Rate Limit / 5xx Outage| J[Automatic Circuit Breaker & Fallback]
    
    J --> K[Route to Secondary Gateway Provider]
    K --> I
```

---

## 2. Model Routing Matrix

| Tier | Target Workloads | Primary Model | Fallback Model | Token Context |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 (High Reasoning)** | Supervisor Planning, Reasoning Agent, Discrepancy Matching | Anthropic Claude 3.5 Sonnet | OpenAI GPT-4o | 200,000 / 128,000 |
| **Tier 2 (Fast Routing)** | Intent Classification, Entity Mapping, Simple Summaries | Anthropic Claude 3.5 Haiku | OpenAI GPT-4o-mini | 200,000 / 128,000 |
| **Tier 3 (Ultra-Long Context)**| Massive Multi-File RAG Ingestion, Full Financial Portfolios | Google Gemini 1.5 Pro | Claude 3.5 Sonnet | 2,000,000 |
| **Tier 4 (Self-Hosted / Local)**| Strict Air-Gapped / Offline On-Premises Deployments | Ollama Llama 3.3 70B | Ollama Mistral Nemo | 128,000 / 32,000 |

---

## 3. Resilience & Circuit Breaker Specification

* **Exponential Backoff:** Retries 429 (Rate Limit) and 503 (Overloaded) with jittered backoff ($1s, 2s, 4s$).
* **Circuit Breaker:** If a provider fails 5 consecutive times within a 60-second sliding window, trips open for 120 seconds and diverts all traffic to the fallback model.
* **Token Usage Metering:** Tracks prompt tokens, completion tokens, and estimated USD cost per tenant in PostgreSQL.
