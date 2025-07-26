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
    update_document_status,
    create_document_entry,
    list_documents,
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
    try:
        doc = await session.get(DocumentModel, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        doc.status = status_update.status
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        return Document.model_validate(doc)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document status: {str(e)}",
        )


@router.post(
    "/{doc_id}/sign",
    response_model=DocumentSignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sign_document(
    doc_id: int,
    sign_request: DocumentSignRequest = Body(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        doc = await session.get(DocumentModel, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Validate that the role is a valid signing role
        if sign_request.role not in SigningRole:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid signing role. Must be one of: {[role.value for role in SigningRole]}",
            )

        # Check if this role has already signed
        existing_signatures = doc.signatures or {}
        if sign_request.role.value in existing_signatures:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document has already been signed by {sign_request.role.value}",
            )

        # Initialize signatures dict if it doesn't exist
        if doc.signatures is None:
            doc.signatures = {}

        # Store signature by role
        doc.signatures[sign_request.role.value] = sign_request.signature
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        return DocumentSignResponse(
            message=f"Signature from {sign_request.role.value} added successfully",
            document_id=doc_id,
            signed_by_role=sign_request.role,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign document: {str(e)}",
        )


@router.get("/{doc_id}", response_model=DocumentWithSigningStatus)
async def get_document_with_signers(
    doc_id: int, session: AsyncSession = Depends(get_session)
):
    try:
        doc = await session.get(DocumentModel, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Get all possible signing roles
        all_roles = [role for role in SigningRole]
        existing_signatures = doc.signatures or {}

        # Convert existing signature keys to SigningRole enums
        signed_by = []
        for role_str in existing_signatures.keys():
            try:
                signed_by.append(SigningRole(role_str))
            except ValueError:
                # Handle legacy role strings that might not match enum
                continue

        # Find unsigned roles
        unsigned_by = [role for role in all_roles if role not in signed_by]

        # Convert document model to schema using model_validate instead of from_orm
        document_data = Document.model_validate(doc)

        return DocumentWithSigningStatus(
            **document_data.model_dump(),
            signed_by=signed_by,
            unsigned_by=unsigned_by,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )
