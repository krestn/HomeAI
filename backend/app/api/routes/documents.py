from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from fastapi.responses import FileResponse

from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.document import DocumentMetadata
from app.services.document_store import document_store

router = APIRouter(prefix="/documents", tags=["documents"])


def _serialize_document(doc: dict) -> DocumentMetadata:
    return DocumentMetadata(
        id=doc["id"],
        original_name=doc.get("original_name", "document.pdf"),
        uploaded_at=doc["uploaded_at"],
        preview=doc.get("preview", ""),
        preview_url=f"/documents/{doc['id']}/file",
    )


@router.get("", response_model=list[DocumentMetadata])
def list_documents(current_user: User = Depends(get_current_user)):
    docs = document_store.list_documents(current_user.id)
    return [_serialize_document(doc) for doc in docs]


@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    metadata = document_store.save_document(
        current_user.id, file.filename or "document.pdf", content
    )
    return _serialize_document(metadata)


@router.get("/{document_id}/file")
def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    pdf_path = document_store.get_pdf_path(current_user.id, document_id)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = document_store.get_document(current_user.id, document_id)
    filename = doc["original_name"] if doc else pdf_path.name
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    success = document_store.delete_document(current_user.id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return Response(status_code=204)
