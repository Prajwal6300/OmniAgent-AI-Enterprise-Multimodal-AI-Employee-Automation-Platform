# RAG Agent — OmniAgent AI

The **RAG Agent** is the specialized enterprise knowledge retrieval and grounded generation agent within the OmniAgent AI platform. It provides factual, source-attributed answers exclusively drawn from verified company documents stored in PostgreSQL with pgvector.

---

## 1. Key Responsibilities & Guarantees

* **Zero-Hallucination Fallback:** If documents do not contain the answer, responds strictly with `"I couldn't find enough information in the available documents to answer this."` Never answers from pre-trained memory.
* **Strict Multi-Tenant Isolation:** Vector searches are enforced at the database level with `organization_id`. Cross-tenant data leaks are impossible.
* **Non-Fabricated Citations:** Source citations link directly to physical chunk IDs, document names, and 1-indexed page numbers.
* **Prompt Injection Defense:** Document contexts are treated as untrusted passive data. System prompts cannot be overridden by embedded document instructions.

---

## 2. Architecture & Pipeline

```text
User Question
      ↓
Supervisor Agent (routes KNOWLEDGE_SEARCH)
      ↓
RAG Agent (LangGraph Workflow)
      ↓
validate_query
      ↓
generate_query_embedding (1536-d float vector)
      ↓
retrieve_chunks (pgvector cosine distance + org_id filter)
      ↓
filter_context (lexical term-matching + thresholding)
      ↓
build_context (injection-safe metadata tags)
      ↓
generate_answer (strictly grounded LLM synthesis)
      ↓
validate_grounding (factuality check)
      ↓
build_citations (verified source links)
      ↓
RAGResponse
```

---

## 3. Usage Example

```python
from agents.rag import RAGAgent

rag_agent = RAGAgent()

response = await rag_agent.query(
    question="What is the company's leave policy?",
    organization_id="org-uuid-1234",
    document_id=None,
    top_k=5
)

print(response.answer)
print(response.grounded)
for citation in response.citations:
    print(f"Source: {citation.document_name}, Page: {citation.page_number}")
```
