from app.enums.document_types import DocumentType
from app.enums.document_status import DocumentStatus
from app.enums.signing_roles import SigningRole
from app.models.document import Document as DocumentModel
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentWithSigningStatus,
    DocumentSignRequest,
    DocumentSignResponse,
    DocumentStatusUpdateRequest,
)
from app.services.document_service import (
    create_document_entry,
    list_documents,
    get_document_with_signing_status,
    update_document_status,
    sign_document,
    request_signatures,
    check_document_completion,
)
from app.services.storage_service import upload_to_s3
from app.core.auth import get_current_user
from app.schemas.user import User
from app.core.db import async_session
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    Body,
    status,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import uuid4
from datetime import date
from typing import List

router = APIRouter()


async def get_session():
    async with async_session() as session:
        yield session


@router.get("/", response_model=List[Document])
async def get_documents(session: AsyncSession = Depends(get_session)):
    return await list_documents(session)


@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    doc_type: DocumentType = Form(...),
    doc_date: date = Form(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        contents = await file.read()
        s3_key = f"docs/{uuid4()}_{file.filename}"

        # Upload to S3 first (this can fail)
        upload_to_s3(contents, s3_key)

        # Create document entry with transaction atomicity
        return await create_document_entry(
            DocumentCreate(
                name=name,
                date=doc_date,
                doc_type=doc_type,
                uploaded_by=current_user.user_id,
            ),
            s3_key,
            session,
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.patch("/{doc_id}/status", response_model=Document)
async def update_status(
    doc_id: int,
    status_update: DocumentStatusUpdateRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    return await update_document_status(doc_id, status_update.status, session)


@router.post(
    "/{doc_id}/sign",
    response_model=DocumentSignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sign_document_endpoint(
    doc_id: int,
    sign_request: DocumentSignRequest = Body(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await sign_document(doc_id, sign_request, user.user_id, session)


@router.get("/{doc_id}", response_model=DocumentWithSigningStatus)
async def get_document_with_signers(
    doc_id: int, session: AsyncSession = Depends(get_session)
):
    return await get_document_with_signing_status(doc_id, session)


@router.post("/{doc_id}/request-signatures")
async def request_document_signatures(
    doc_id: int, session: AsyncSession = Depends(get_session)
):
    return await request_signatures(doc_id, session)


@router.get("/{doc_id}/completion-status")
async def get_document_completion_status(
    doc_id: int, session: AsyncSession = Depends(get_session)
):
    return await check_document_completion(doc_id, session)
