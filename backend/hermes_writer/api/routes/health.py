from fastapi import APIRouter, Request

from hermes_writer import __version__

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    store = request.app.state.file_store
    profile_store = request.app.state.profile_store
    return {
        "status": "ok",
        "version": __version__,
        "storage_available": store.is_available(),
        "profiles_count": profile_store.count_profiles(),
    }
