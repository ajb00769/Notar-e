from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.document import Document as DocumentModel
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentWithSigningStatus,
    DocumentSignRequest,
    DocumentSignResponse,
)
from app.enums.document_status import DocumentStatus
from app.enums.signing_roles import SigningRole
from app.enums.user_roles import UserRole
from app.services.storage_service import generate_presigned_get_url
from app.core.hashing import generate_sha256_hash
from app.services.blockchain_service import notarize_document
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
import httpx


async def create_document_entry(
    doc_data: DocumentCreate,
    s3_key: str,
    session: AsyncSession,
) -> Document:
    """Create a new document entry with blockchain notarization."""
    try:
        # Fetch the file for hashing via signed URL
        url = generate_presigned_get_url(s3_key)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            file_bytes = response.content

        # Generate document hash
        doc_hash = generate_sha256_hash(file_bytes)
        blob_uri = f"s3://your-s3-bucket/{s3_key}"

        # Notarize on blockchain
        await notarize_document(
            document_hash=doc_hash,
            blob_uri=blob_uri,
            doc_type=doc_data.doc_type,
            user_id=doc_data.uploaded_by,
        )

        # Save to DB
        db_doc = DocumentModel(
            name=doc_data.name,
            upload_date=doc_data.date,
            doc_type=doc_data.doc_type,
            uploaded_by=doc_data.uploaded_by,
            blob_uri=blob_uri,
            document_hash=doc_hash,
        )
        session.add(db_doc)
        await session.commit()
        await session.refresh(db_doc)

        return Document.model_validate(db_doc)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


async def list_documents(
    session: AsyncSession, user_id: str, user_role: UserRole
) -> List[Document]:
    """List documents based on user role and participation."""
    try:
        # Admins and superadmins can see all documents
        if user_role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            docs = await session.exec(select(DocumentModel))
            return [Document.model_validate(doc) for doc in docs.all()]
        # Other users: only documents they own or participate in
        else:
            # Documents where user is the owner
            owner_stmt = select(DocumentModel).where(
                DocumentModel.uploaded_by == user_id
            )
            owner_docs = await session.exec(owner_stmt)
            owner_docs_list = owner_docs.all()

            # Documents where user is a participant (signed or needs to sign)
            # Assuming signatures is a dict with user_id in the value
            participant_stmt = select(DocumentModel)
            participant_docs = await session.exec(participant_stmt)
            participant_docs_list = [
                doc
                for doc in participant_docs.all()
                if doc.signatures
                and any(
                    sig.get("user_id") == user_id for sig in doc.signatures.values()
                )
            ]

            # Combine and deduplicate
            all_docs = {doc.id: doc for doc in owner_docs_list + participant_docs_list}
            return [Document.model_validate(doc) for doc in all_docs.values()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


async def get_document_by_id(
    doc_id: int, session: AsyncSession
) -> Optional[DocumentModel]:
    """Get a document by ID."""
    try:
        doc = await session.get(DocumentModel, doc_id)
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )


async def get_document_with_signing_status(
    doc_id: int, session: AsyncSession
) -> DocumentWithSigningStatus:
    """Get document with signing status information."""
    try:
        doc = await get_document_by_id(doc_id, session)
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

        # Convert document model to schema
        document_data = Document.model_validate(doc)

        return DocumentWithSigningStatus(
            **document_data.model_dump(),
            signed_by=signed_by,
            unsigned_by=unsigned_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document with signing status: {str(e)}",
        )


async def update_document_status(
    doc_id: int, new_status: DocumentStatus, session: AsyncSession
) -> Document:
    """Update document status."""
    try:
        doc = await get_document_by_id(doc_id, session)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        doc.status = new_status
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        return Document.model_validate(doc)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document status: {str(e)}",
        )


async def sign_document(
    doc_id: int, sign_request: DocumentSignRequest, user_id: str, session: AsyncSession
) -> DocumentSignResponse:
    """Sign a document with the specified role."""
    try:
        doc = await get_document_by_id(doc_id, session)
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

        # Store signature by role with audit trail
        doc.signatures[sign_request.role.value] = {
            "signature": sign_request.signature,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        return DocumentSignResponse(
            message=f"Signature from {sign_request.role.value} added successfully",
            document_id=doc_id,
            signed_by_role=sign_request.role,
        )
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign document: {str(e)}",
        )


async def request_signatures(doc_id: int, session: AsyncSession) -> dict:
    """Request signatures from all required parties for a document."""
    try:
        doc = await get_document_by_id(doc_id, session)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Get unsigned roles
        doc_with_status = await get_document_with_signing_status(doc_id, session)
        unsigned_roles = doc_with_status.unsigned_by

        if not unsigned_roles:
            return {
                "message": "All required signatures have been collected",
                "document_id": doc_id,
                "status": "complete",
            }

        # TODO: Implement actual signature request logic
        # This could involve:
        # - Sending emails/notifications to required signers
        # - Creating signing sessions
        # - Generating signing links
        # - Scheduling video meetings for notarization

        return {
            "message": f"Signature requests sent to {len(unsigned_roles)} parties",
            "document_id": doc_id,
            "pending_roles": [role.value for role in unsigned_roles],
            "status": "pending_signatures",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request signatures: {str(e)}",
        )


async def check_document_completion(doc_id: int, session: AsyncSession) -> dict:
    """Check if document has all required signatures and update status accordingly."""
    try:
        doc_with_status = await get_document_with_signing_status(doc_id, session)

        # Check if all required roles have signed
        required_roles = {
            SigningRole.NOTARY,
            SigningRole.AFFIANT,
            SigningRole.WITNESS,
            SigningRole.GRANTOR,
        }
        signed_roles = set(doc_with_status.signed_by)

        is_complete = required_roles.issubset(signed_roles)

        if is_complete and doc_with_status.status != DocumentStatus.COMPLETED:
            # Update document status to completed
            await update_document_status(doc_id, DocumentStatus.COMPLETED, session)

        return {
            "document_id": doc_id,
            "is_complete": is_complete,
            "signed_by": [role.value for role in signed_roles],
            "missing_signatures": [
                role.value for role in (required_roles - signed_roles)
            ],
            "status": (
                DocumentStatus.COMPLETED.value
                if is_complete
                else DocumentStatus.PENDING.value
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check document completion: {str(e)}",
        )
