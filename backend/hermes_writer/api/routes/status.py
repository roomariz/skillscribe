from fastapi import APIRouter, Request

from hermes_writer import __version__
from hermes_writer.api.schemas import SuccessEnvelope

router = APIRouter(prefix="/api")


@router.get("/version")
async def version() -> SuccessEnvelope:
    return SuccessEnvelope(data={"version": __version__})


@router.get("/status")
async def status(request: Request) -> SuccessEnvelope:
    store = request.app.state.file_store
    settings = request.app.state.settings
    return SuccessEnvelope(
        data={
            "storage_path": settings.storage_root.as_posix(),
            "storage_available": store.is_available(),
            "database_type": "file-based",
            "profiles_count": store.count_profiles(),
            "documents_count": 0,
            "skills_count": 0,
            "privacy_mode": settings.privacy_mode,
        }
    )

