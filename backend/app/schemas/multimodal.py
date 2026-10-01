from typing import Any

from pydantic import BaseModel


class BoundingBox(BaseModel):
    box_2d: list[float] # [ymin, xmin, ymax, xmax]
    label: str
    confidence: float

class MultimodalAnalysisRequest(BaseModel):
    media_type: str # IMAGE, AUDIO, VIDEO, PDF
    media_url_or_path: str
    prompt: str | None = None

class MultimodalAnalysisResponse(BaseModel):
    transcription_or_text: str | None = None
    summary: str | None = None
    bounding_boxes: list[BoundingBox] | None = None
    metadata: dict[str, Any] = {}
