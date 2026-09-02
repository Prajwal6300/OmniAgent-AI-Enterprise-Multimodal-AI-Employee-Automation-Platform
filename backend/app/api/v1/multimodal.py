from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.multimodal_service import MultimodalService
from app.schemas.multimodal import MultimodalAnalysisRequest, MultimodalAnalysisResponse
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/multimodal", tags=["Multimodal"])

@router.post("/analyze", response_model=ResponseEnvelope[MultimodalAnalysisResponse])
async def analyze_multimodal(
    request: MultimodalAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    service = MultimodalService()
    res = await service.analyze(request)
    return ResponseEnvelope(data=res)
