from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class BoundingBox(BaseModel):
    box_2d: List[float] # [ymin, xmin, ymax, xmax]
    label: str
    confidence: float

class MultimodalAnalysisRequest(BaseModel):
    media_type: str # IMAGE, AUDIO, VIDEO, PDF
    media_url_or_path: str
    prompt: Optional[str] = None

class MultimodalAnalysisResponse(BaseModel):
    transcription_or_text: Optional[str] = None
    summary: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    metadata: Dict[str, Any] = {}
