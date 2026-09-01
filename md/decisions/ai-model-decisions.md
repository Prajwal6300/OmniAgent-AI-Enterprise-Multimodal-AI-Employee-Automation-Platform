# Architecture Decision Records — ADR 003: Hybrid Foundation Model Strategy

## Status
**Status:** ✅ ACCEPTED & IMPLEMENTED

---

## 1. Context & Problem Statement
Enterprises have conflicting requirements: complex multi-step reasoning requires frontier models (Claude 3.5 Sonnet / GPT-4o), high-volume routine tasks require low-cost latency-optimized models (Claude 3.5 Haiku / GPT-4o-mini), and regulated or sovereign environments require fully offline air-gapped models.

---

## 2. Decision: Dynamic 4-Tier Model Gateway
We implemented an intelligent abstraction layer that dynamically routes requests to the optimal foundation model based on task complexity, privacy tier, and operational budgets.

### Model Tier Allocations
1. **Tier 1 (Frontier Reasoning):** Anthropic Claude 3.5 Sonnet (Supervisor, Reasoning, 3-Way Match).
2. **Tier 2 (Fast Routing & Extraction):** Anthropic Claude 3.5 Haiku / GPT-4o-mini (Intent classification, entity normalization).
3. **Tier 3 (Long-Context Analytics):** Google Gemini 1.5 Pro (2M token multi-document portfolios).
4. **Tier 4 (Air-Gapped Local):** Local Ollama Llama 3.3 70B / Qwen 2.5 Coder (On-premises deployments).
