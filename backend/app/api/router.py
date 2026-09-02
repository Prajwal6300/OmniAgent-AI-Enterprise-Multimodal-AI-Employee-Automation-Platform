from fastapi import APIRouter
from app.api.v1 import (
    auth, users, chat, documents, multimodal,
    agents, workflows, approvals, notifications,
    integrations, analytics, health
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
