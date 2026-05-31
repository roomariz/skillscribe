from fastapi import APIRouter, Request

from hermes_writer.api.schemas import SuccessEnvelope

router = APIRouter(prefix="/api/profiles/{profile_id}/skills")


@router.get("")
async def list_skills(request: Request, profile_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.skill_store.list_skills(profile_id))


@router.get("/{skill_id}")
async def get_skill(request: Request, profile_id: str, skill_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.skill_store.get_skill(profile_id, skill_id))


@router.post("/{skill_id}/approve")
async def approve_skill(request: Request, profile_id: str, skill_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.skill_store.approve_skill(profile_id, skill_id))


@router.post("/{skill_id}/activate")
async def activate_skill(request: Request, profile_id: str, skill_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.skill_store.activate_skill(profile_id, skill_id))


@router.post("/{skill_id}/set-default")
async def set_default_skill(request: Request, profile_id: str, skill_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.skill_store.set_default_skill(profile_id, skill_id))
