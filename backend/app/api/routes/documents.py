from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.document import Document as DocumentModel, DocumentCreate, DocumentWithSigningStatus
from app.enums.document_status import DocumentStatus
from app.services.document_service import get_documents, create_document, update_document_status
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import async_session
from app.schemas.document import Document, DocumentCreate, DocumentType
from app.services.document_service import create_document_entry, list_documents
from app.services.storage_service import upload_to_s3
from uuid import uuid4
from app.core.auth import get_current_user
from app.schemas.user import User

router = APIRouter()

def get_session():
    async with async_session() as session:
        yield session

@router.get("/", response_model=List[Document])
async def list_documents():
    return get_documents()

@router.patch("/{doc_id}/status", response_model=Document)
async def update_status(doc_id: int, status: DocumentStatus):
    updated = update_document_status(doc_id, status.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Document not found")

@router.get("/", response_model=list[Document])
async def get_documents(session: AsyncSession = Depends(get_session)):
    return await list_documents(session)

@router.post("/", response_model=Document)
async def upload_document(
        file: UploadFile = File(...),
        name: str = Form(...),
        doc_type: DocumentType = Form(...),
        date: str = Form(...),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    contents = await file.read()
    s3_key = f"docs/{uuid4()}_{file.filename}"
    upload_to_s3(contents, s3_key)
    return await create_document_entry(
        DocumentCreate(name=name, date=date, doc_type=doc_type, uploaded_by=current_user.user_id),
        s3_key,
        session
    )

@router.post("/{doc_id}/sign")
async def sign_document(
        doc_id: int,
        role: str = Form(...),               # e.g. "notary", "affiant", "witness"
        signature: str = Form(...),          # user signs document hash client-side
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    doc = await session.get(DocumentModel, doc_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")

    # Signatures are stored by role
    doc.signatures[role] = signature
    session.add(doc)
    await session.commit()
    return {"message": f"Signature from {role} added"}

@router.get("/{doc_id}", response_model=DocumentWithSigningStatus)
async def get_document_with_signers(
        doc_id: int,
        session: AsyncSession = Depends(get_session)
):
    doc = await session.get(DocumentModel, doc_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")

    roles = ["notary", "affiant", "witness", "other_signer"]
    existing = doc.signatures or {}

    return {
        **Document.from_orm(doc).dict(),
        "signed_by": list(existing.keys()),
        "unsigned_by": [r for r in roles if r not in existing]
    }
