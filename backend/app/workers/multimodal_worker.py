from app.core.logging import logger

def process_multimodal_task(media_id: str, media_type: str):
    logger.info("worker_processing_multimodal", media_id=media_id, media_type=media_type)
    return {"status": "SUCCESS", "media_id": media_id}
