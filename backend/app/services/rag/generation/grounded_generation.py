from typing import Any


class GroundedGenerator:
    def construct_context_prompt(self, query: str, context_chunks: list[dict[str, Any]]) -> str:
        formatted = "\n\n".join([f"[{c.get('id')}] {c.get('content')}" for c in context_chunks])
        return f"Enterprise Context:\n{formatted}\n\nQuery: {query}\nAnswer with explicit citations:"
