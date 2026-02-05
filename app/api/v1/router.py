from fastapi import APIRouter

from app.api.v1.endpoints import ocr, health, auth

api_router = APIRouter()

api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])

api_router.include_router(health.router, prefix="/health", tags=["Health"])

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
