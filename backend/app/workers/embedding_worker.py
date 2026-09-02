from app.core.logging import logger

def generate_embeddings_task(document_id: str):
    logger.info("worker_generating_embeddings", document_id=document_id)
    return {"status": "SUCCESS", "document_id": document_id}
