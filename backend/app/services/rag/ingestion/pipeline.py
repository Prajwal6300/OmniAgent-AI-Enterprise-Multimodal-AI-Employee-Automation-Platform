from app.services.rag.ingestion.loader import DocumentLoader
from app.services.rag.ingestion.chunker import TextChunker
from app.services.rag.ingestion.metadata import MetadataExtractor

class IngestionPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.metadata_extractor = MetadataExtractor()

    def run(self, file_path: str):
        docs = self.loader.load(file_path)
        chunks = []
        for doc in docs:
            raw_chunks = self.chunker.chunk(doc["text"])
            for idx, text in enumerate(raw_chunks):
                meta = self.metadata_extractor.enrich(text, doc)
                chunks.append({"index": idx, "content": text, "metadata": meta})
        return chunks
