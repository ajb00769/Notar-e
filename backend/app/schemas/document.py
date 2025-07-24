from pydantic import BaseModel, HttpUrl
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict

class DocumentType(str, Enum):
    affidavit = "Affidavit"
    deed = "Deed"
    contract = "Contract"
    power_of_attorney = "PowerOfAttorney"

class DocumentStatus(str, Enum):
    pending = "Pending"
    completed = "Completed"
    needs_action = "Needs Action"

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
        orm_mode = True

class DocumentWithSigningStatus(Document):
    signed_by: List[str]
    unsigned_by: List[str]
