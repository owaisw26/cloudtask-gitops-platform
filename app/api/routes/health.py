from fastapi import APIRouter
from fastapi import status
from fastapi.responses import JSONResponse

from app.core.database import check_db_connection

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {
        "status": "ok"
    }

@router.get("/ready")
def ready():
    if not check_db_connection():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return {
        "status": "ready"
    }
