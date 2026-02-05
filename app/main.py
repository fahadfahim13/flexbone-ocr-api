from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.logging import setup_logging, get_logger, CloudLoggingMiddleware
from app.core.exceptions import AppException
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1.router import api_router
from app.schemas.common import ErrorResponse, ErrorDetail, ResponseMetadata

settings = get_settings()

setup_logging(log_level=settings.log_level, json_format=not settings.debug)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        auth_enabled=settings.auth_enabled,
        rate_limit_enabled=settings.rate_limit_enabled,
    )
    yield
    logger.info("application_shutting_down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## OCR Text Extraction API

Extract text from images using Google Cloud Vision API.

### Features
- Upload JPG/PNG/GIF images up to 10MB
- Batch processing for multiple images
- Get extracted text with confidence scores
- Intelligent caching for identical images
- Text preprocessing and cleanup
- Optional JWT authentication
- Rate limiting support
- Production-grade Cloud Logging
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(CloudLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    from app.core.logging import get_request_id

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details),
            metadata=ResponseMetadata(
                request_id=get_request_id() or "unknown", processing_time_ms=0
            ),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    from app.core.logging import get_request_id

    logger.exception("unhandled_exception", error=str(exc))

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={"error": str(exc)} if settings.debug else {},
            ),
            metadata=ResponseMetadata(
                request_id=get_request_id() or "unknown", processing_time_ms=0
            ),
        ).model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs"""
    return {"message": "Welcome to Flexbone OCR API", "docs": "/docs"}
