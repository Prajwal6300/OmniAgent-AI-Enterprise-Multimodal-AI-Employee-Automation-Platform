from typing import Dict, Any
from app.schemas.multimodal import MultimodalAnalysisRequest, MultimodalAnalysisResponse

class MultimodalService:
    async def analyze(self, request: MultimodalAnalysisRequest) -> MultimodalAnalysisResponse:
        return MultimodalAnalysisResponse(
            summary=f"Processed media {request.media_type}",
            metadata={"source": request.media_url_or_path}
        )
