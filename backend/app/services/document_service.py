from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.document import Document as DocumentModel
from app.models.document_signature_audit import DocumentSignatureAudit
from app.models.user import Users
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentWithSigningStatus,
    DocumentSignRequest,
    DocumentSignResponse,
)
from app.schemas.signature import SignatureEntry
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
from app.utils.locks import document_lock
from app.utils.signing_roles import get_required_signing_roles


async def create_document_entry(
    doc_data: DocumentCreate,
    s3_key: str,
    session: AsyncSession,
) -> Document:
    """Create a new document entry with blockchain notarization."""
    from app.services.storage_service import delete_from_s3
    import logging

    db_doc = None
    file_uploaded = False
    try:
        # Fetch the file for hashing via signed URL
        url = generate_presigned_get_url(s3_key)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            file_bytes = response.content
        file_uploaded = True

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

        # Save to DB in a transaction
        async with session.begin():
            db_doc = DocumentModel(
                name=doc_data.name,
                upload_date=doc_data.date,
                doc_type=doc_data.doc_type,
                uploaded_by=doc_data.uploaded_by,
                blob_uri=blob_uri,
                document_hash=doc_hash,
            )
            session.add(db_doc)
        await session.refresh(db_doc)
        return Document.model_validate(db_doc)
    except Exception as e:
        await session.rollback()
        if file_uploaded:
            try:
                delete_from_s3(s3_key)
            except Exception as cleanup_err:
                logging.error(f"Failed to cleanup S3 file {s3_key}: {cleanup_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


async def list_documents(
    session: AsyncSession,
    user_id: int,
    user_role: UserRole,
    limit: int = 20,
    offset: int = 0,
) -> List[Document]:
    """List documents based on user role and participation, with pagination."""
    try:
        # Admins and superadmins can see all documents
        if user_role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            docs = await session.exec(select(DocumentModel).limit(limit).offset(offset))
            return [Document.model_validate(doc) for doc in docs.all()]
        # Other users: only documents they own or participate in
        else:
            # Documents where user is the owner
            owner_stmt = select(DocumentModel).where(
                DocumentModel.uploaded_by == user_id
            )
            owner_docs = await session.exec(owner_stmt)  # type: ignore
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
            # Apply pagination to the combined results
            paginated_docs = list(all_docs.values())[offset : offset + limit]
            return [Document.model_validate(doc) for doc in paginated_docs]
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


@document_lock(doc_id_arg="doc_id")
async def sign_document(
    doc_id: int,
    sign_request: DocumentSignRequest,
    user_id: int,
    session: AsyncSession,
) -> DocumentSignResponse:
    """Sign a document with the specified role, enforcing signing authorization."""

    allowed_roles = {
        UserRole.NOTARY: [SigningRole.NOTARY],
        UserRole.USER: [
            SigningRole.AFFIANT,
            SigningRole.WITNESS,
            SigningRole.GRANTOR,
            SigningRole.GRANTEE,
            SigningRole.OTHER_SIGNER,
        ],
        UserRole.ADMIN: list(SigningRole),
        UserRole.SUPER_ADMIN: list(SigningRole),
    }

    try:
        db_user = await session.get(Users, user_id)

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        user_role = (
            db_user.role
            if isinstance(db_user.role, UserRole)
            else UserRole(db_user.role)
        )

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

        # Convert user_role to enum if needed
        if not isinstance(user_role, UserRole):
            user_role = UserRole(user_role)

        if sign_request.role not in allowed_roles.get(user_role, []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with role '{user_role.value}' is not authorized to sign as '{sign_request.role.value}'",
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
        doc.signatures[sign_request.role.value] = SignatureEntry(
            signature=sign_request.signature,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
        )

        # Audit log
        audit_entry = DocumentSignatureAudit(
            document_id=doc_id,
            user_id=user_id,
            role=sign_request.role.value,
            timestamp=datetime.now(timezone.utc),
            action="signed",
        )
        session.add(doc)
        session.add(audit_entry)
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
        required_roles = get_required_signing_roles(doc_with_status.doc_type)
        signed_roles = set(role.value for role in doc_with_status.signed_by)

        is_complete = required_roles.issubset(signed_roles)

        if is_complete and doc_with_status.status != DocumentStatus.COMPLETED:
            # Update document status to completed
            await update_document_status(doc_id, DocumentStatus.COMPLETED, session)

        return {
            "document_id": doc_id,
            "is_complete": is_complete,
            "signed_by": list(signed_roles),
            "missing_signatures": list(required_roles - signed_roles),
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
