from typing import List, Optional
from pydantic import BaseModel

class VisionDetection(BaseModel):
    label: str
    confidence: float
    bbox: Optional[List[float]] = None

class VisionResult(BaseModel):
    observations: List[str]
    detections: List[VisionDetection] = []
