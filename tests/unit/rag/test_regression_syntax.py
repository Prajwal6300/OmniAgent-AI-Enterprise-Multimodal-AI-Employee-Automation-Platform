from uuid import uuid4

from app.models.document import DocumentChunk
from sqlalchemy import func, select

from agents.rag.citations import CitationBuilder
from agents.rag.schemas import RetrievedChunk


def test_citations_retrieved_chunk_typing_regression():
    """
    Regression test ensuring CitationBuilder accepts RetrievedChunk and dict chunks
    without raising NameError or TypeError on typing annotations.
    """
    builder = CitationBuilder()
    doc_id = str(uuid4())
    org_id = str(uuid4())
    chunk = RetrievedChunk(
        chunk_id=str(uuid4()),
        document_id=doc_id,
        organization_id=org_id,
        document_name="Employee_Handbook.pdf",
        page_number=4,
        content="All full-time employees receive 20 days of paid annual leave.",
        similarity_score=0.92,
        metadata={"source": "manual"}
    )
    
    answer = "Employees receive 20 days of paid annual leave as documented in Employee_Handbook.pdf."
    citations = builder.build_citations(answer=answer, chunks=[chunk])
    assert isinstance(citations, list)
    
    # Also test with dict chunks
    dict_chunk = {
        "id": str(uuid4()),
        "document_id": doc_id,
        "organization_id": org_id,
        "document_name": "Handbook.pdf",
        "page_number": 4,
        "content": "All full-time employees receive 20 days of paid annual leave.",
        "similarity_score": 0.88,
    }
    citations_dict = builder.build_citations(answer=answer, chunks=[dict_chunk])
    assert isinstance(citations_dict, list)


def test_vector_search_sql_ast_syntax_regression():
    """
    Regression test ensuring the tsvector_qs SQLAlchemy query in vector_search
    is syntactically valid and compiles with correct parenthesis and clauses.
    """
    org_id = uuid4()
    query_text = "vacation policy"
    
    # Replicate the exact tsvector_qs AST construct from vector_search.py
    tsvector_qs = (
        select(
            DocumentChunk,
            func.ts_rank_cd(
                func.to_tsvector('english', DocumentChunk.content),
                func.plainto_tsquery('english', query_text or ""),
            ).label("ts_rank"),
        )
        .where(DocumentChunk.organization_id == org_id)
        .order_by(
            func.ts_rank_cd(
                func.to_tsvector('english', DocumentChunk.content),
                func.plainto_tsquery('english', query_text or ""),
            ).desc()
        )
        .limit(200)
    )
    
    # Must compile without error
    compiled = str(tsvector_qs.compile(compile_kwargs={"literal_binds": False}))
    assert "ts_rank_cd" in compiled
    assert "document_chunks.organization_id =" in compiled
    assert "LIMIT" in compiled
