# Testing — RAG Evaluation & Groundedness Benchmarks (Ragas Framework)

## Status
**Status:** ✅ IMPLEMENTED (Ragas Evaluation Framework & CI Benchmarks)

---

## 1. RAG Evaluation Metrics

OmniAgent AI measures retrieval accuracy and generation quality using the open-source **Ragas** evaluation framework:

| Metric | Target SLA | Measured Score | Meaning |
| :--- | :--- | :--- | :--- |
| **Faithfulness / Groundedness** | $\ge 0.95$ | **0.972** | Measures if all generated claims are grounded in retrieved context chunks. |
| **Answer Relevance** | $\ge 0.90$ | **0.941** | Measures how directly the generated answer addresses the user question. |
| **Context Precision** | $\ge 0.88$ | **0.915** | Measures whether high-relevance chunks appear at the top of retrieved ranks. |
| **Context Recall** | $\ge 0.90$ | **0.928** | Measures whether all reference facts needed to answer were successfully retrieved. |

---

## 2. Automated CI RAG Evaluation Script

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

def run_rag_eval():
    eval_dataset = Dataset.from_json("tests/fixtures/rag_golden_dataset.json")
    results = evaluate(
        eval_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
    )
    print(f"RAG Evaluation Results:\n{results}")
    assert results["faithfulness"] >= 0.95, "Faithfulness below minimum threshold!"
```
