from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import RequestTraceMiddleware
from app.core.exceptions import BaseAppException
from app.api.router import api_router

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Middleware
app.add_middleware(RequestTraceMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    logger.error("application_error", error=exc.message, details=exc.details, path=request.url.path)
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("server_startup", environment=settings.ENVIRONMENT)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("server_shutdown")
