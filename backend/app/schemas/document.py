from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import Optional, Dict, List
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType
from app.enums.signing_roles import SigningRole


class DocumentCreate(BaseModel):
    name: str
    date: date
    doc_type: DocumentType
    uploaded_by: int  # user ID


class Document(DocumentCreate):
    id: int
    status: DocumentStatus
    blob_uri: HttpUrl
    document_hash: str
    signed_blob_uri: Optional[HttpUrl] = None  # S3 URI of the signed PDF
    signed_document_hash: Optional[str] = None  # Hash of the signed PDF
    signatures: Optional[Dict[str, str]] = None

    class ConfigDict:
        from_attributes = True


class DocumentWithSigningStatus(Document):
    signed_by: List[SigningRole]
    unsigned_by: List[SigningRole]


class DocumentSignRequest(BaseModel):
    role: SigningRole
    signature: str


class DocumentSignResponse(BaseModel):
    message: str
    document_id: int
    signed_by_role: SigningRole


class DocumentStatusUpdateRequest(BaseModel):
    status: DocumentStatus
