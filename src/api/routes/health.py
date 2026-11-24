"""GET /health — usado por orquestradores de container (ECS/Docker) para health-check."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "parser-engine"}
