from backend.app.services.rag.ingestion.chunker import TextChunker

def test_text_chunker_bounds():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    sample_text = "OmniAgent AI " * 20
    chunks = chunker.chunk(sample_text)
    assert len(chunks) > 1
    assert len(chunks[0]) <= 100
