from fastapi import APIRouter, Request, Response

from hermes_writer.api.schemas import ProfileCreateRequest, ProfileUpdateRequest, SuccessEnvelope

router = APIRouter(prefix="/api/profiles")


@router.post("", status_code=201)
async def create_profile(request: Request, payload: ProfileCreateRequest) -> SuccessEnvelope:
    profile = request.app.state.profile_store.create_profile(
        profile_id=payload.profile_id,
        display_name=payload.display_name,
        description=payload.description,
    )
    return SuccessEnvelope(data=profile)


@router.get("")
async def list_profiles(request: Request) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.profile_store.list_profiles())


@router.get("/{profile_id}")
async def get_profile(request: Request, profile_id: str) -> SuccessEnvelope:
    profile = request.app.state.profile_store.get_profile(profile_id)
    profile["documents"] = request.app.state.document_store.list_documents(profile_id)
    profile["skills"] = request.app.state.skill_store.list_skills(profile_id)
    return SuccessEnvelope(data=profile)


@router.put("/{profile_id}")
async def update_profile(
    request: Request,
    profile_id: str,
    payload: ProfileUpdateRequest,
) -> SuccessEnvelope:
    profile = request.app.state.profile_store.update_profile(
        profile_id,
        display_name=payload.display_name,
        description=payload.description,
        default_skill=payload.default_skill,
    )
    return SuccessEnvelope(data=profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(request: Request, profile_id: str) -> Response:
    request.app.state.profile_store.soft_delete_profile(profile_id)
    return Response(status_code=204)
