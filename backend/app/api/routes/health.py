from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Service health check")
async def read_health() -> dict[str, str]:
    return {"status": "ok"}
