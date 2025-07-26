from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import Optional, Dict, List
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType


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
    signed_by: List[str]
    unsigned_by: List[str]
