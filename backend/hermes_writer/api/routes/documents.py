from fastapi import APIRouter, File, Request, UploadFile

from hermes_writer.api.errors import ApiError
from hermes_writer.api.schemas import ExtractedTextUpdateRequest, SuccessEnvelope

router = APIRouter(prefix="/api/profiles/{profile_id}/documents")


@router.post("/upload", status_code=201)
async def upload_document(
    request: Request,
    profile_id: str,
    file: UploadFile = File(...),
) -> SuccessEnvelope:
    if not file.filename:
        raise ApiError("INVALID_FILENAME", "Uploaded file must have a filename.")
    content = await file.read()
    document = request.app.state.document_store.upload_document(profile_id, file.filename, content)
    return SuccessEnvelope(data=document)


@router.get("")
async def list_documents(
    request: Request,
    profile_id: str,
    status: str | None = None,
) -> SuccessEnvelope:
    documents = request.app.state.document_store.list_documents(profile_id, status=status)
    return SuccessEnvelope(data=documents)


@router.get("/{doc_id}")
async def get_document(request: Request, profile_id: str, doc_id: str) -> SuccessEnvelope:
    return SuccessEnvelope(data=request.app.state.document_store.get_document(profile_id, doc_id))


@router.get("/{doc_id}/preview")
async def preview_document(request: Request, profile_id: str, doc_id: str) -> SuccessEnvelope:
    preview = request.app.state.document_store.preview_extracted_text(profile_id, doc_id)
    return SuccessEnvelope(data=preview)


@router.put("/{doc_id}")
async def update_document_text(
    request: Request,
    profile_id: str,
    doc_id: str,
    payload: ExtractedTextUpdateRequest,
) -> SuccessEnvelope:
    document = request.app.state.document_store.update_extracted_text(
        profile_id,
        doc_id,
        payload.extracted_text,
    )
    return SuccessEnvelope(data=document)


@router.put("/{doc_id}/extracted-text")
async def update_extracted_text(
    request: Request,
    profile_id: str,
    doc_id: str,
    payload: ExtractedTextUpdateRequest,
) -> SuccessEnvelope:
    document = request.app.state.document_store.update_extracted_text(
        profile_id,
        doc_id,
        payload.extracted_text,
    )
    return SuccessEnvelope(data=document)
