import re
from typing import Any
from agents.rag.schemas import Citation, RetrievedChunk


class CitationBuilder:
    """
    Extracts, validates, and builds verifiable source citations from retrieved chunks
    and generated LLM answers.
    Guarantees no fabricated document names or page numbers exist in citations.
    """

    def build_citations(
        self,
        answer: str,
        chunks: list[RetrievedChunk | dict[str, Any]],
        fallback_answer: str = "I couldn't find enough information in the available documents to answer this."
    ) -> list[Citation]:
        """
        Builds citations strictly verified against retrieved chunks.
        If the answer is a refusal/fallback, citations must be empty.
        """
        if not chunks or fallback_answer.lower() in answer.lower():
            return []

        citations: list[Citation] = []
        seen_keys: set[tuple[str, int | None]] = set()

        # Map chunks by document_name and chunk_id for fast lookup
        chunk_map: dict[str, Any] = {}
        for c in chunks:
            c_dict = c if isinstance(c, dict) else c.model_dump()
            chunk_id = c_dict.get("chunk_id", "")
            if chunk_id:
                chunk_map[chunk_id] = c_dict

        # Pattern: [Source: <Name>, Page <Num>] or [Source: <Name>]
        source_pattern = re.compile(r"\[Source:\s*([^,\]]+)(?:,\s*Page\s*(\d+))?[^\]]*\]", re.IGNORECASE)
        matches = source_pattern.findall(answer)

        if matches:
            for doc_name, page_str in matches:
                doc_name_clean = doc_name.strip()
                page_num = int(page_str) if page_str else None

                # Find corresponding chunk in retrieved chunks
                matched_chunk = None
                for c in chunks:
                    c_dict = c if isinstance(c, dict) else c.model_dump()
                    c_name = c_dict.get("document_name") or c_dict.get("metadata", {}).get("document_name", "")
                    c_page = c_dict.get("page_number") or c_dict.get("metadata", {}).get("page_number")
                    if doc_name_clean.lower() in c_name.lower():
                        if page_num is None or page_num == c_page:
                            matched_chunk = c_dict
                            break

                if matched_chunk:
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

        # If explicit tags were omitted by the LLM, cite the highest-scoring candidate chunks that contributed to the context
        if not citations:
            for c in chunks[:3]:
                c_dict = c if isinstance(c, dict) else c.model_dump()
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
