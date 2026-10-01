from fastapi import APIRouter

from app.api.v1 import (
    agents,
    analytics,
    approvals,
    auth,
    chat,
    documents,
    health,
    integrations,
    multimodal,
    notifications,
    orchestration,
    users,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(multimodal.router)
api_router.include_router(agents.router)
api_router.include_router(workflows.router)
api_router.include_router(approvals.router)
api_router.include_router(notifications.router)
api_router.include_router(integrations.router)
api_router.include_router(analytics.router)
api_router.include_router(orchestration.router)
