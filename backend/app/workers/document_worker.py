from app.core.logging import logger

def process_document_task(document_id: str):
    logger.info("worker_processing_document", document_id=document_id)
    return {"status": "SUCCESS", "document_id": document_id}
