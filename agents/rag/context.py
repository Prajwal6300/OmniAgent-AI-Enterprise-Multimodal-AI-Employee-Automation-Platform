from typing import Any
from agents.rag.schemas import RetrievedChunk


class ContextBuilder:
    """
    Dedicated Context Construction Engine.
    Converts retrieved semantic chunks into an injection-resistant, formatted context string
    with explicit document and page metadata tags.
    """

    def __init__(self, max_context_chars: int = 15000):
        self.max_context_chars = max_context_chars

    def build_context(self, chunks: list[RetrievedChunk | dict[str, Any]]) -> str:
        """
        Formats retrieved passages into a structured, isolated context block.
        """
        if not chunks:
            return ""

        formatted_blocks: list[str] = []
        seen_texts: set[str] = set()
        total_chars = 0

        for chunk in chunks:
            if isinstance(chunk, dict):
                content = chunk.get("content", "").strip()
                doc_name = chunk.get("document_name") or chunk.get("metadata", {}).get("document_name", "Document")
                page_num = chunk.get("page_number") or chunk.get("metadata", {}).get("page_number")
                section = chunk.get("section") or chunk.get("metadata", {}).get("section")
                chunk_id = chunk.get("chunk_id", "")
            else:
                content = chunk.content.strip()
                doc_name = chunk.document_name
                page_num = chunk.page_number
                section = chunk.section
                chunk_id = chunk.chunk_id

            if not content:
                continue

            # Deduplication safeguard: avoid passing identical passages
            content_hash = hash(content[:100])
            if content_hash in seen_texts:
                continue
            seen_texts.add(content_hash)

            # Sanitize any attempted tag breakout or system prompt override inside document text
            sanitized_content = (
                content.replace("</context>", "[context_tag]")
                .replace("<context>", "[context_tag]")
                .replace("```system", "```doc_text")
            )

            # Format source label
            source_parts = [f"Source: {doc_name}"]
            if page_num:
                source_parts.append(f"Page {page_num}")
            if section:
                source_parts.append(f"Section: {section}")
            if chunk_id:
                source_parts.append(f"Chunk ID: {chunk_id}")

            source_header = " | ".join(source_parts)

            block = f"[{source_header}]\n{sanitized_content}"

            if total_chars + len(block) > self.max_context_chars:
                # Add truncated notice if budget exceeded
                break

            formatted_blocks.append(block)
            total_chars += len(block)

        return "\n\n---\n\n".join(formatted_blocks)
