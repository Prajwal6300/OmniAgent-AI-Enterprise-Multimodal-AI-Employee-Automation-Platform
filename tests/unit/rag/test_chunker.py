from backend.app.services.rag.ingestion.chunker import TextChunker


def test_text_chunker_bounds():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    sample_text = "OmniAgent AI " * 20
    chunks = chunker.chunk(sample_text)
    assert len(chunks) > 1
    assert len(chunks[0]) <= 100


def test_text_chunker_empty():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    assert chunker.chunk("") == []


def test_chunk_pages_preserves_page_numbers():
    chunker = TextChunker(chunk_size=150, chunk_overlap=20)
    pages = [
        {"page_number": 1, "text": "Page 1: Annual leave policy details. Employees receive 25 paid vacation days per calendar year."},
        {"page_number": 2, "text": "Page 2: Sick leave policy. Employees are entitled to 10 days paid sick leave with medical documentation."},
    ]
    chunks = chunker.chunk_pages(pages)
    assert len(chunks) >= 2
    assert any(c["page_number"] == 1 for c in chunks)
    assert any(c["page_number"] == 2 for c in chunks)
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


def test_chunk_pages_preserves_sections():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    pages = [
        {"page_number": 1, "text": "Safety Instructions: All technicians must wear safety goggles and ear protection before operating the lathe machine."},
    ]
    sections = [
        {"title": "Safety Instructions", "section_type": "heading"}
    ]
    chunks = chunker.chunk_pages(pages, sections=sections)
    assert len(chunks) >= 1
    assert chunks[0]["section"] == "Safety Instructions"
    assert "safety goggles" in chunks[0]["content"]
