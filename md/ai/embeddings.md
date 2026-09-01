# AI Subsystems — Vector Embeddings & Similarity Search

## Status
**Status:** ✅ IMPLEMENTED (Dense pgvector + Sparse Lexical Embeddings)

---

## 1. Vector Embedding Models & Dimensions

OmniAgent AI leverages standardized dense vector representations paired with cosine similarity metrics for semantic retrieval.

| Metric | Primary Self-Hosted Model | Alternative Cloud Provider Model |
| :--- | :--- | :--- |
| **Model Name** | `BAAI/bge-large-en-v1.5` | OpenAI `text-embedding-3-large` |
| **Embedding Dimensions** | 1,024 dimensions | 1,536 / 3,072 dimensions |
| **Distance Metric** | Cosine Distance ($1 - \cos(\theta)$) | Cosine Distance |
| **Context Window** | 512 tokens | 8,191 tokens |
| **MTEB Benchmark Rank** | Top 5 Open-Source Dense | Top Tier Commercial |
| **Deployment Mode** | Local FastEmbed / ONNX Runtime / PyTorch | REST API (`/v1/embeddings`) |

---

## 2. Mathematical Similarity Formulation

For a normalized query vector $\vec{q}$ and document chunk vector $\vec{d}$, cosine similarity is computed as:
$$\text{Sim}(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\|_2 \|\vec{d}\|_2} = \sum_{i=1}^{n} q_i d_i$$

In PostgreSQL `pgvector`, this is evaluated using the `<=>` cosine distance operator:
$$\text{Distance} = 1 - \text{Sim}(\vec{q}, \vec{d})$$

---

## 3. Embedding Cache Optimization

To eliminate redundant embedding generation for identical queries across enterprise users:
* An in-memory **Redis Embedding Cache** stores the SHA-256 hash of recent search queries mapped to their float vector array.
* Average query cache hit latency is **< 1.5 ms**, reducing model inference costs and API rate consumption.
