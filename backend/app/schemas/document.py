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
    uploaded_by: str  # user ID or email


class Document(DocumentCreate):
    id: int
    status: DocumentStatus
    blob_uri: HttpUrl
    document_hash: str
    signatures: Optional[Dict[str, str]] = None

    class Config:
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
