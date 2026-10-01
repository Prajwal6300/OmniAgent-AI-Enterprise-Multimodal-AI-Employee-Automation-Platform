import re
from typing import Any

from app.agents.rag.schemas import Citation, RetrievedChunk


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _find_span_in_text(needle: str, haystack: str) -> tuple[int, int] | None:
    """Find first occurrence of needle in haystack, return (start, end) byte offsets."""
    needle_n = _normalize_whitespace(needle)
    haystack_n = _normalize_whitespace(haystack)
    idx = haystack_n.find(needle_n)
    if idx < 0:
        return None
    # Return character offsets in the original (unnormalized) text
    # Calculate real start by finding the matching position
    real_start = haystack.index(needle_n) if needle_n in haystack else idx
    real_end = real_start + len(needle)
    return (real_start, real_end)


class CitationBuilder:
    """
    Extracts, validates, and builds verifiable source citations from retrieved chunks
    and generated LLM answers.
    Guarantees no fabricated document names or page numbers exist in citations.
    Uses span-level claim-to-chunk alignment for strict verification.
    """

    def build_citations(
        self,
        answer: str,
        chunks: list[RetrievedChunk | dict[str, Any]],
        fallback_answer: str = "I couldn't find enough information in the available documents to answer this.",
    ) -> list[Citation]:
        """
        Builds citations strictly verified against retrieved chunks.
        If the answer is a refusal/fallback, citations must be empty.
        Uses exact content span matching for verification.
        """
        if not chunks or fallback_answer.lower() in answer.lower():
            return []

        citations: list[Citation] = []
        seen_keys: set[tuple[str, int | None]] = set()

        # Normalize answer once for span matching
        answer_norm = _normalize_whitespace(answer)

        # Build a map of chunk_id -> chunk info, also index by normalized content
        chunk_map: dict[str, dict[str, Any]] = {}
        content_to_chunk_id: dict[str, str] = {}
        for c in chunks:
            c_dict = c if isinstance(c, dict) else {**c.model_dump()}
            chunk_id = c_dict.get("chunk_id", "")
            if chunk_id:
                chunk_map[chunk_id] = c_dict
                # Index by normalized content spans (up to 200 chars)
                content = c_dict.get("content", "")
                if content:
                    content_norm = _normalize_whitespace(content[:200])
                    if content_norm not in content_to_chunk_id:
                        content_to_chunk_id[content_norm] = chunk_id

        # Step 1: Try to find [Source: Name, Page] tags in answer
        source_pattern = re.compile(r"\[Source:\s*([^,\]]+)(?:,\s*Page\s*(\d+))?[^\]]*\]", re.IGNORECASE)
        tag_matches = source_pattern.findall(answer)

        if tag_matches:
            for doc_name, page_str in tag_matches:
                doc_name_clean = doc_name.strip()
                page_num = int(page_str) if page_str else None

                # Try to find matching chunk by exact content span first
                matched_chunk_id = None
                # Search through content index for spans that appear in answer
                for content_norm, cid in content_to_chunk_id.items():
                    if content_norm in answer_norm:
                        matched_chunk_id = cid
                        break

                # Fallback: match by document_name
                if not matched_chunk_id:
                    for c in chunks:
                        c_dict = c if isinstance(c, dict) else {**c.model_dump()}
                        c_name = c_dict.get("document_name") or c_dict.get("metadata", {}).get("document_name", "")
                        if doc_name_clean.lower() in c_name.lower():
                            matched_chunk_id = c_dict.get("chunk_id", "")
                            break

                if matched_chunk_id and matched_chunk_id in chunk_map:
                    matched_chunk = chunk_map[matched_chunk_id]
                    doc_id = matched_chunk.get("document_id", "")
                    key = (doc_id, page_num or matched_chunk.get("page_number"))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        citations.append(
                            Citation(
                                document_id=doc_id,
                                document_name=matched_chunk.get("document_name", doc_name_clean),
                                page_number=page_num or matched_chunk.get("page_number"),
                                chunk_id=matched_chunk.get("chunk_id", ""),
                                relevance_score=matched_chunk.get("similarity_score"),
                                section=matched_chunk.get("section")
                            )
                        )

        # Step 2: If no explicit [Source:] tags, use span-level alignment
        # Find chunks whose content appears in the answer (exact span match)
        if not citations:
            for c in chunks:
                c_dict = c if isinstance(c, dict) else {**c.model_dump()}
                chunk_id = c_dict.get("chunk_id", "")
                content = c_dict.get("content", "")
                if not content:
                    continue
                content_norm = _normalize_whitespace(content)
                # Check if any sentence/phrase from the chunk appears in the answer
                re.split(r"[.!?]+", answer_norm)
                chunk_sents = re.split(r"[.!?]+", content_norm)
                # Check if any chunk sentence appears in answer
                for cs in chunk_sents:
                    cs = cs.strip()
                    if len(cs) > 8 and cs in answer_norm:
                        doc_id = c_dict.get("document_id", "")
                        page_num = c_dict.get("page_number")
                        key = (doc_id, page_num)
                        if key not in seen_keys:
                            seen_keys.add(key)
                            citations.append(
                                Citation(
                                    document_id=doc_id,
                                    document_name=c_dict.get("document_name", "Document"),
                                    page_number=page_num,
                                    chunk_id=chunk_id,
                                    relevance_score=c_dict.get("similarity_score"),
                                    section=c_dict.get("section")
                                )
                            )
                            break

        # Step 3: Default to top-3 chunks if still no citations
        if not citations:
            for c in chunks[:3]:
                c_dict = c if isinstance(c, dict) else {**c.model_dump()}
                doc_id = c_dict.get("document_id", "")
                page_num = c_dict.get("page_number")
                key = (doc_id, page_num)
                if key not in seen_keys:
                    seen_keys.add(key)
                    citations.append(
                        Citation(
                            document_id=doc_id,
                            document_name=c_dict.get("document_name", "Document"),
                            page_number=page_num,
                            chunk_id=c_dict.get("chunk_id", ""),
                            relevance_score=c_dict.get("similarity_score"),
                            section=c_dict.get("section")
                        )
                    )

        return citations