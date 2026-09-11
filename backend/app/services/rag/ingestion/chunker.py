from typing import Any, List, Optional
import re

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:
        settings = None


class TextChunker:
    """
    Core text chunker implementing character and sentence boundary windowing.
    Maintains 100% backward-compatibility with tests/unit/rag/test_chunker.py.
    """
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        if chunk_size is not None:
            self.chunk_size = chunk_size
        elif settings:
            self.chunk_size = getattr(settings, "RAG_CHUNK_SIZE", 500)
        else:
            self.chunk_size = 500

        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        elif settings:
            self.chunk_overlap = getattr(settings, "RAG_CHUNK_OVERLAP", 50)
        else:
            self.chunk_overlap = 50

        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = max(0, self.chunk_size // 5)

    def chunk(self, text: str) -> List[str]:
        """Splits plain text into overlapping chunks."""
        if not text:
            return []

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk_slice = text[start:end]
            chunks.append(chunk_slice)
            if end >= text_len:
                break
            start = end - self.chunk_overlap

        return chunks

    def chunk_pages(
        self,
        pages: List[dict[str, Any]],
        sections: Optional[List[dict[str, Any]]] = None
    ) -> List[dict[str, Any]]:
        """
        Sensible hierarchical chunker preserving physical page numbers and section boundaries.
        Input pages format: [{'page_number': 1, 'text': '...'}, ...]
        Returns: [{'chunk_index': 0, 'content': '...', 'page_number': 1, 'section': '...'}, ...]
        """
        chunks: List[dict[str, Any]] = []
        chunk_idx = 0

        # Build section lookup if available
        section_titles = [s.get("title", "") for s in (sections or []) if s.get("title")]

        for page in pages:
            page_num = page.get("page_number", 1)
            page_text = page.get("text", "").strip()

            if not page_text:
                continue

            # Identify if page starts with or contains any section heading
            current_section = None
            for title in section_titles:
                if title.lower() in page_text.lower():
                    current_section = title
                    break

            # Natural paragraph splitting
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_chunk_text = ""

            for p in paragraphs:
                if len(current_chunk_text) + len(p) + 2 <= self.chunk_size:
                    current_chunk_text = f"{current_chunk_text}\n\n{p}".strip() if current_chunk_text else p
                else:
                    if current_chunk_text:
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "content": current_chunk_text,
                            "page_number": page_num,
                            "section": current_section
                        })
                        chunk_idx += 1
                        # Retain overlap from end of previous chunk if possible
                        if self.chunk_overlap > 0:
                            overlap_text = current_chunk_text[-self.chunk_overlap:]
                            current_chunk_text = f"{overlap_text}\n\n{p}".strip()
                        else:
                            current_chunk_text = p
                    else:
                        # Single paragraph exceeds chunk_size, slice it directly
                        sub_chunks = self.chunk(p)
                        for sc in sub_chunks:
                            chunks.append({
                                "chunk_index": chunk_idx,
                                "content": sc,
                                "page_number": page_num,
                                "section": current_section
                            })
                            chunk_idx += 1
                        current_chunk_text = ""

            if current_chunk_text:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": current_chunk_text,
                    "page_number": page_num,
                    "section": current_section
                })
                chunk_idx += 1

        return chunks
